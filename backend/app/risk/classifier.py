import logging
from typing import Dict, Any, List, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

class RiskClassifier:
    """
    Core Contribution: Multi-Factor Risk Assessment Engine.
    Evaluates business and operational risk prior to any remediation action.
    
    Factors Evaluated:
    1. Environment Tag (production vs staging vs dev)
    2. Attachment / Topology Dependencies (Load Balancer, Cluster, Active Mounts)
    3. Action Type & Destructiveness (Delete vs Stop vs Schedule vs Release)
    4. Detection Confidence & Utilization Variance
    
    Routing:
    - LOW (< 35): Safe for automated remediation
    - MEDIUM (35 - 69): Routed to Human Approval Queue
    - HIGH (>= 70): Critical Risk -> Routed to Approval Queue with strict warnings
    """

    @classmethod
    def evaluate(
        cls,
        finding: Dict[str, Any],
        resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        points = 0.0
        factors = []

        env = (resource.get("environment_tag") or "unknown").lower()
        tags = resource.get("tags", {})
        extra = resource.get("extra_metadata", {})
        r_type = resource.get("resource_type")
        action = finding.get("recommended_action")
        avg_cpu = float(resource.get("average_cpu", 0.0))
        detector_type = finding.get("detector_type")

        # -----------------------------------------------------------------
        # Factor 1: Environment Tag Impact (Max ~45 pts)
        # -----------------------------------------------------------------
        if env in ("production", "prod", "critical", "live"):
            f_pts = 45.0
            f_reason = "Production/Mission-Critical environment: blast radius directly affects customer operations or revenue."
        elif env in ("staging", "stage", "uat", "preprod"):
            f_pts = 20.0
            f_reason = "Staging/Pre-production environment: blast radius limited to integration testing."
        elif env in ("dev", "test", "sandbox"):
            f_pts = 5.0
            f_reason = "Dev/Test/Sandbox environment: minimal operational blast radius."
        else:
            f_pts = 25.0
            f_reason = "Untagged/Unknown environment: conservative risk posture applied."

        points += f_pts
        factors.append({
            "factor_name": "Environment Impact",
            "points": f_pts,
            "weight_pct": 40.0,
            "reason": f_reason
        })

        # -----------------------------------------------------------------
        # Factor 2: Topology & Attachment Dependency (Max ~35 pts)
        # -----------------------------------------------------------------
        attached_to_lb = extra.get("attached_to_lb", False)
        attachments_count = extra.get("attachments_count", 0)

        if attached_to_lb:
            f_pts = 35.0
            f_reason = "Resource is active behind an Application Load Balancer or Ingress Gateway."
        elif attachments_count > 0:
            f_pts = 25.0
            f_reason = f"Resource has {attachments_count} active storage/compute mount dependencies."
        elif r_type == "block_storage" and extra.get("is_unattached", True):
            f_pts = 0.0
            f_reason = "Standalone volume is verified unattached to any compute host."
        elif r_type == "ip_address" and not extra.get("is_associated", False):
            f_pts = 0.0
            f_reason = "Public IP is verified unassociated with any network interface."
        else:
            f_pts = 10.0
            f_reason = "No high-risk network topology dependencies detected."

        points += f_pts
        factors.append({
            "factor_name": "Topology & Dependencies",
            "points": f_pts,
            "weight_pct": 30.0,
            "reason": f_reason
        })

        # -----------------------------------------------------------------
        # Factor 3: Action Destructiveness & Resource Type (Max ~25 pts)
        # -----------------------------------------------------------------
        if action == "delete_volume":
            f_pts = 20.0
            f_reason = "Deletion of storage volume requested. Mandatory pre-action snapshot required."
        elif action == "stop_instance":
            f_pts = 15.0
            f_reason = "State change from running to stopped. Can be restarted if required."
        elif action == "release_ip":
            f_pts = 5.0
            f_reason = "Releasing unallocated public IP address."
        elif action == "schedule_stop":
            f_pts = 5.0
            f_reason = "Non-destructive off-hours schedule configuration."
        else:
            f_pts = 10.0
            f_reason = f"Action '{action}' evaluated."

        points += f_pts
        factors.append({
            "factor_name": "Action Impact",
            "points": f_pts,
            "weight_pct": 20.0,
            "reason": f_reason
        })

        # -----------------------------------------------------------------
        # Factor 4: Detection Confidence & Metric Variance (Max ~10 pts)
        # -----------------------------------------------------------------
        if detector_type == "ml_anomaly":
            f_pts = 10.0
            f_reason = "ML Anomaly detection output requires human validation before auto-action."
        elif r_type == "compute_instance" and avg_cpu > 8.0:
            # CPU is near the 10% cutoff
            f_pts = 10.0
            f_reason = f"CPU utilization ({avg_cpu:.1f}%) is close to the 10% threshold boundary."
        elif r_type == "block_storage" and resource.get("state") == "unattached":
            f_pts = -5.0 # High confidence reduction
            f_reason = "Definitive unattached state confirmed by cloud provider metadata."
        else:
            f_pts = 0.0
            f_reason = "Standard heuristic rule detection confidence."

        points += f_pts
        factors.append({
            "factor_name": "Detection Confidence",
            "points": f_pts,
            "weight_pct": 10.0,
            "reason": f_reason
        })

        # Bound score between 0 and 100
        final_score = max(0.0, min(100.0, round(points, 1)))

        # Categorize
        if final_score < settings.RISK_LOW_MAX:
            risk_level = "LOW"
            requires_approval = False
            summary = "Low Risk: Safe for automated remediation without manual intervention."
        elif final_score < settings.RISK_MED_MAX:
            risk_level = "MEDIUM"
            requires_approval = True
            summary = "Medium Risk: Routed to human approval queue due to staging environment or service state change."
        else:
            risk_level = "HIGH"
            requires_approval = True
            summary = "High Risk: Critical impact detected (production workload, active dependency, or high blast radius). Requires mandatory human approval."

        return {
            "risk_score": final_score,
            "risk_level": risk_level,
            "requires_approval": requires_approval,
            "summary": summary,
            "factors": factors
        }
