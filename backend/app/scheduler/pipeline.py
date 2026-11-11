import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import Account, Resource, Finding, Approval, RemediationAction, AuditLog, SavingsHistory
from app.connectors import get_connector
from app.normalizer import CloudNormalizer
from app.detection import RuleEngine, MLAnomalyDetector
from app.risk import RiskClassifier
from app.executor import RemediationExecutor, RemediationVerifier

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Core Pipeline Orchestrator coordinating all 7 layers:
    Accounts -> Collection -> Normalization -> Detection (Rules & ML) ->
    Risk Classification -> Routing (Auto vs Approval) -> Execution & Verification
    """

    @classmethod
    def run_pipeline_for_account(cls, db: Session, account: Account) -> Dict[str, Any]:
        logger.info(f"Initiating CloudOptima scan for account: {account.name} ({account.provider})")
        db.add(AuditLog(
            event_type="SCAN_STARTED",
            actor="pipeline_orchestrator",
            provider=account.provider,
            details={"account_id": account.account_id, "name": account.name}
        ))
        db.commit()

        connector = get_connector(
            provider=account.provider,
            account_id=account.account_id
        )

        # -------------------------------------------------------------
        # Layer 2: Collection
        # -------------------------------------------------------------
        raw_instances = connector.list_compute_instances()
        raw_volumes = connector.list_storage_volumes()
        raw_ips = connector.list_ip_addresses()
        cost_history = connector.get_cost_history(days=30)

        # -------------------------------------------------------------
        # Layer 3: Normalization & Persistence
        # -------------------------------------------------------------
        normalized_resources = []
        
        for inst in raw_instances:
            norm = CloudNormalizer.normalize_instance(inst, account.provider, account.account_id)
            normalized_resources.append(norm)

        for vol in raw_volumes:
            norm = CloudNormalizer.normalize_volume(vol, account.provider, account.account_id)
            normalized_resources.append(norm)

        for ip in raw_ips:
            norm = CloudNormalizer.normalize_ip(ip, account.provider, account.account_id)
            normalized_resources.append(norm)

        # Upsert normalized resources in DB
        db_resources: Dict[str, Resource] = {}
        for r_dict in normalized_resources:
            res_id = r_dict["resource_id"]
            existing = db.query(Resource).filter(Resource.resource_id == res_id).first()
            if existing:
                for k, v in r_dict.items():
                    setattr(existing, k, v)
                db_resources[res_id] = existing
            else:
                new_res = Resource(**r_dict)
                db.add(new_res)
                db.flush()
                db_resources[res_id] = new_res

        db.commit()

        # -------------------------------------------------------------
        # Layer 4: Detection (Rule Engine + ML Anomaly Detector)
        # -------------------------------------------------------------
        raw_findings: List[Dict[str, Any]] = []

        # 4a. Heuristic Rules
        for r_dict in normalized_resources:
            rule_findings = RuleEngine.evaluate_resource(r_dict)
            raw_findings.extend(rule_findings)

        # 4b. ML Cost Spike Anomaly Detection (Isolation Forest)
        ml_detector = MLAnomalyDetector()
        if cost_history:
            ml_cost_findings = ml_detector.detect_cost_spikes(cost_history, account.provider, account.account_id)
            for f in ml_cost_findings:
                # Store anomaly dummy resource if not already present
                raw_res = f.pop("raw_resource")
                a_id = raw_res["resource_id"]
                existing_anomaly = db.query(Resource).filter(Resource.resource_id == a_id).first()
                if existing_anomaly:
                    existing_anomaly.monthly_cost = raw_res["monthly_cost"]
                    existing_anomaly.extra_metadata = raw_res.get("extra_metadata", {})
                    db_resources[a_id] = existing_anomaly
                else:
                    anomaly_res = Resource(
                        account_id=account.account_id,
                        provider=account.provider,
                        resource_id=a_id,
                        name=f"Anomaly: {account.provider.upper()} Cost Surge",
                        resource_type="cost_anomaly",
                        region="global",
                        environment_tag="production",
                        monthly_cost=raw_res["monthly_cost"],
                        state="active",
                        extra_metadata=raw_res.get("extra_metadata", {})
                    )
                    db.add(anomaly_res)
                    db.flush()
                    db_resources[a_id] = anomaly_res
                raw_findings.append(f)

        # 4c. ML Multivariate Waste Anomaly Detection
        ml_multi_findings = ml_detector.detect_multivariate_resource_anomalies(normalized_resources)
        for f in ml_multi_findings:
            f.pop("raw_resource", None)
            raw_findings.append(f)

        # -------------------------------------------------------------
        # Layer 5: Risk Classification & Routing
        # -------------------------------------------------------------
        findings_created = 0
        auto_remediated = 0
        approvals_queued = 0

        for f_data in raw_findings:
            res_id = f_data["resource_id"]
            db_res = db_resources.get(res_id)
            if not db_res:
                continue

            # Convert db_res to dict for evaluation
            res_info = {
                "resource_id": db_res.resource_id,
                "resource_type": db_res.resource_type,
                "environment_tag": db_res.environment_tag,
                "average_cpu": db_res.average_cpu,
                "monthly_cost": db_res.monthly_cost,
                "state": db_res.state,
                "tags": db_res.tags or {},
                "extra_metadata": db_res.extra_metadata or {}
            }

            # Evaluate Risk Score
            risk_result = RiskClassifier.evaluate(finding=f_data, resource=res_info)

            # Check if existing finding already recorded
            existing_finding = db.query(Finding).filter(
                Finding.resource_id == res_id,
                Finding.category == f_data["category"],
                Finding.status.in_(["open", "pending_approval", "approved", "remediating"])
            ).first()

            if existing_finding:
                finding_obj = existing_finding
                finding_obj.estimated_monthly_saving = f_data["estimated_monthly_saving"]
                finding_obj.risk_score = risk_result["risk_score"]
                finding_obj.risk_level = risk_result["risk_level"]
                finding_obj.risk_breakdown = risk_result
            else:
                finding_obj = Finding(
                    resource_id=res_id,
                    provider=f_data["provider"],
                    detector_type=f_data["detector_type"],
                    category=f_data["category"],
                    reason=f_data["reason"],
                    recommended_action=f_data["recommended_action"],
                    estimated_monthly_saving=f_data["estimated_monthly_saving"],
                    risk_score=risk_result["risk_score"],
                    risk_level=risk_result["risk_level"],
                    risk_breakdown=risk_result,
                    status="open"
                )
                db.add(finding_obj)
                db.flush()
                findings_created += 1

            # ---------------------------------------------------------
            # Routing Decision: Low Risk -> Auto-Remediate, Else -> Approval
            # ---------------------------------------------------------
            if risk_result["risk_level"] == "LOW" and account.auto_remediate_low_risk:
                logger.info(f"Auto-remediating low-risk finding {finding_obj.id} on {res_id}")
                action = RemediationAction(
                    finding_id=finding_obj.id,
                    resource_id=res_id,
                    action_type=finding_obj.recommended_action,
                    status="approved",
                    triggered_by="auto_remediator"
                )
                db.add(action)
                db.flush()

                # Layer 6: Execution & Verification
                RemediationExecutor.execute(db, action, finding_obj, db_res, dry_run=False)
                RemediationVerifier.verify(db, action, finding_obj, db_res)
                auto_remediated += 1
            else:
                # Route to human approval queue
                existing_approval = db.query(Approval).filter(Approval.finding_id == finding_obj.id).first()
                if not existing_approval:
                    finding_obj.status = "pending_approval"
                    approval = Approval(
                        finding_id=finding_obj.id,
                        status="pending",
                        requested_by="risk_classifier",
                        decision_notes=f"Risk Score: {risk_result['risk_score']} ({risk_result['risk_level']}). {risk_result['summary']}"
                    )
                    db.add(approval)
                    approvals_queued += 1

        # Finalize scan
        account.last_scanned_at = datetime.now(timezone.utc)
        db.add(AuditLog(
            event_type="SCAN_COMPLETED",
            actor="pipeline_orchestrator",
            provider=account.provider,
            details={
                "account_id": account.account_id,
                "discovered_resources": len(normalized_resources),
                "findings_count": len(raw_findings),
                "auto_remediated": auto_remediated,
                "approvals_queued": approvals_queued
            }
        ))
        db.commit()

        return {
            "account_id": account.account_id,
            "provider": account.provider,
            "discovered_resources": len(normalized_resources),
            "findings_detected": len(raw_findings),
            "auto_remediated": auto_remediated,
            "approvals_queued": approvals_queued
        }
