import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class RuleEngine:
    """
    Heuristic Rule Engine detecting explicit cloud waste across 4 core scenarios:
    1. Unattached storage volumes
    2. Unused / unassociated Elastic/Public IPs
    3. Low-utilization compute instances (<10% CPU over 7 days)
    4. Non-production compute instances running 24/7 outside working hours
    """

    @classmethod
    def evaluate_resource(cls, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        r_type = resource.get("resource_type")
        state = resource.get("state")
        env = resource.get("environment_tag", "unknown")
        cost = float(resource.get("monthly_cost", 0.0))
        res_id = resource.get("resource_id")
        provider = resource.get("provider", "aws")
        extra = resource.get("extra_metadata", {})
        tags = resource.get("tags", {})

        # Rule 1: Unattached Storage Volumes
        if r_type == "block_storage" and state == "unattached":
            size_gb = extra.get("size_gb", 100)
            savings = max(cost, round(size_gb * 0.10, 2))
            findings.append({
                "resource_id": res_id,
                "provider": provider,
                "detector_type": "rule_engine",
                "category": "unattached_volume",
                "reason": f"Unattached storage volume ({size_gb} GB) detected with no active compute attachment, incurring idle storage charges.",
                "recommended_action": "delete_volume",
                "estimated_monthly_saving": savings,
                "raw_resource": resource
            })

        # Rule 2: Unused / Unassociated Elastic IPs
        if r_type == "ip_address" and state == "unassociated":
            ip_val = extra.get("public_ip", res_id)
            savings = max(cost, 4.50)
            findings.append({
                "resource_id": res_id,
                "provider": provider,
                "detector_type": "rule_engine",
                "category": "unused_ip",
                "reason": f"Public IP address {ip_val} is unassociated and accruing idle reservation fees without routing traffic.",
                "recommended_action": "release_ip",
                "estimated_monthly_saving": savings,
                "raw_resource": resource
            })

        # Rule 3: Idle / Underutilized Instances (<10% CPU for 7 days)
        if r_type == "compute_instance" and state == "running":
            avg_cpu = float(resource.get("average_cpu", 0.0))
            if avg_cpu < 10.0:
                est_saving = round(cost * 0.90, 2)
                findings.append({
                    "resource_id": res_id,
                    "provider": provider,
                    "detector_type": "rule_engine",
                    "category": "idle_instance",
                    "reason": f"Compute instance '{resource.get('name')}' sustained only {avg_cpu:.1f}% average CPU utilization over the past 7 days (threshold: <10%).",
                    "recommended_action": "stop_instance",
                    "estimated_monthly_saving": est_saving,
                    "raw_resource": resource
                })

        # Rule 4: Non-Production Resources Running Outside Working Hours
        if r_type == "compute_instance" and state == "running" and env in ("dev", "test", "staging", "sandbox"):
            # Check if auto-off schedule tag is absent
            has_schedule = any(k.lower() in ("schedule", "auto-stop", "business-hours") for k in tags.keys())
            if not has_schedule:
                # 65% monthly savings by shutting down off-work hours (nights + weekends = 118 hrs/week out of 168)
                off_hours_savings = round(cost * 0.65, 2)
                findings.append({
                    "resource_id": res_id,
                    "provider": provider,
                    "detector_type": "rule_engine",
                    "category": "off_hours_dev",
                    "reason": f"Non-production ({env}) instance '{resource.get('name')}' is active 24/7 without an off-hours schedule. Turning off outside business hours saves ~65% monthly cost.",
                    "recommended_action": "schedule_stop",
                    "estimated_monthly_saving": off_hours_savings,
                    "raw_resource": resource
                })

        return findings
