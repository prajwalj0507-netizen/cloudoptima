import logging
from typing import Dict, Any
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
from app.models import RemediationAction, Finding, Resource, SavingsHistory, AuditLog
from app.connectors import get_connector
from app.executor.rollback import RollbackManager

logger = logging.getLogger(__name__)

class RemediationVerifier:
    """
    Verification Engine.
    Re-checks cloud resource state post-execution.
    Confirms nothing unintended was impacted.
    On success: marks 'verified', updates finding to 'remediated', and commits realized savings.
    On failure: automatically triggers rollback to restore pre-action state.
    """

    @classmethod
    def verify(
        cls,
        db: Session,
        action: RemediationAction,
        finding: Finding,
        resource: Resource
    ) -> RemediationAction:
        if action.dry_run:
            action.status = "verified"
            action.verified_at = datetime.now(timezone.utc)
            action.verification_result = {"verified": True, "dry_run": True, "note": "Simulation verified."}
            db.commit()
            return action

        connector = get_connector(provider=finding.provider, account_id=resource.account_id)
        
        # Expected post-action state
        expected_state_map = {
            "stop_instance": "stopped",
            "delete_volume": "deleted",
            "release_ip": "released",
            "schedule_stop": "active"
        }
        expected_state = expected_state_map.get(action.action_type, "verified")

        try:
            verif_res = connector.verify_resource_state(resource.resource_id, expected_state)
            is_verified = verif_res.get("verified", False)

            if is_verified:
                action.status = "verified"
                action.verified_at = datetime.now(timezone.utc)
                action.verification_result = verif_res

                # Update finding status
                finding.status = "remediated"
                finding.resolved_at = datetime.now(timezone.utc)

                # Record realized savings in savings_history
                today = date.today()
                savings_record = db.query(SavingsHistory).filter(
                    SavingsHistory.date == today,
                    SavingsHistory.provider == finding.provider,
                    SavingsHistory.category == finding.category
                ).first()

                if not savings_record:
                    savings_record = SavingsHistory(
                        date=today,
                        provider=finding.provider,
                        category=finding.category,
                        realized_savings=finding.estimated_monthly_saving,
                        projected_savings=finding.estimated_monthly_saving
                    )
                    db.add(savings_record)
                else:
                    savings_record.realized_savings += finding.estimated_monthly_saving
                    savings_record.projected_savings = max(0.0, savings_record.projected_savings - finding.estimated_monthly_saving)

                db.add(AuditLog(
                    event_type="REMEDIATION_ACTION_VERIFIED",
                    actor="verifier",
                    resource_id=resource.resource_id,
                    provider=finding.provider,
                    details={
                        "action_id": action.id,
                        "realized_monthly_savings": finding.estimated_monthly_saving,
                        "verification_details": verif_res
                    }
                ))
                db.commit()
                logger.info(f"Remediation action {action.id} successfully verified.")

            else:
                logger.warning(f"Verification failed for action {action.id}. Initiating automated rollback.")
                action.status = "verification_failed"
                action.verification_result = verif_res
                db.commit()

                # Trigger automated rollback
                RollbackManager.rollback(
                    db=db,
                    action=action,
                    finding=finding,
                    resource=resource,
                    reason="Automated rollback: post-action verification failed expected state criteria."
                )

        except Exception as e:
            logger.error(f"Verifier exception for action {action.id}: {e}")
            action.status = "verification_failed"
            action.error_message = f"Verifier error: {str(e)}"
            db.commit()
            RollbackManager.rollback(
                db=db,
                action=action,
                finding=finding,
                resource=resource,
                reason=f"Verifier execution error: {str(e)}"
            )

        return action
