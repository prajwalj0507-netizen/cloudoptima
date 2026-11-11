import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class CloudNormalizer:
    """
    Universal Multi-Cloud Resource Normalizer.
    Converts provider-specific schemas (AWS EC2/EBS/EIP, Azure VM/Disks/PIP, GCP GCE/PD)
    into a standardized schema:
    [provider, resource_id, type, region, environment_tag, avg_cpu, avg_mem, monthly_cost, last_activity, state, extra_metadata]
    """

    @staticmethod
    def extract_environment(tags: Dict[str, Any]) -> str:
        """Extracts and normalizes environment classification from tags."""
        if not tags:
            return "unknown"
        
        # Check standard casing variants
        env_val = (
            tags.get("Environment") or 
            tags.get("environment") or 
            tags.get("env") or 
            tags.get("ENV") or 
            tags.get("Tier") or 
            tags.get("Stage") or 
            ""
        ).lower()

        if "prod" in env_val or "production" in env_val or "live" in env_val or "critical" in env_val:
            return "production"
        elif "stage" in env_val or "staging" in env_val or "uat" in env_val or "preprod" in env_val:
            return "staging"
        elif "test" in env_val or "qa" in env_val:
            return "test"
        elif "dev" in env_val or "development" in env_val or "sandbox" in env_val:
            return "dev"
        return "unknown"

    @classmethod
    def normalize_instance(cls, raw: Dict[str, Any], provider: str, account_id: str) -> Dict[str, Any]:
        tags = raw.get("tags", {})
        env = cls.extract_environment(tags)
        
        # Standardize state
        state = str(raw.get("state", "unknown")).lower()
        if state in ("running", "in-use"):
            normalized_state = "running"
        elif state in ("stopped", "deallocated", "terminated"):
            normalized_state = "stopped"
        else:
            normalized_state = state

        return {
            "account_id": account_id,
            "provider": provider.lower(),
            "resource_id": str(raw.get("raw_id")),
            "name": raw.get("name") or raw.get("raw_id"),
            "resource_type": "compute_instance",
            "region": raw.get("region", "global"),
            "environment_tag": env,
            "average_cpu": float(raw.get("average_cpu", 0.0)),
            "average_memory": float(raw.get("average_memory", 0.0)),
            "monthly_cost": float(raw.get("monthly_cost", 0.0)),
            "last_activity": raw.get("launch_time") or datetime.now(timezone.utc),
            "state": normalized_state,
            "tags": tags,
            "extra_metadata": {
                "instance_type": raw.get("instance_type", "unknown"),
                "vcpus": int(raw.get("vcpus", 4)),
                "memory_gb": float(raw.get("memory_gb", 16.0)),
                "network_in_gb": round(float(raw.get("network_in_gb", 0.0)), 2),
                "network_out_gb": round(float(raw.get("network_out_gb", 0.0)), 2),
                "data_transfer_gb": round(float(raw.get("data_transfer_gb", float(raw.get("network_in_gb", 0.0)) + float(raw.get("network_out_gb", 0.0)))), 2),
                "attached_to_lb": bool(raw.get("attached_to_lb", False)),
                "raw_state": state
            }
        }

    @classmethod
    def normalize_volume(cls, raw: Dict[str, Any], provider: str, account_id: str) -> Dict[str, Any]:
        tags = raw.get("tags", {})
        env = cls.extract_environment(tags)

        # Standardize state
        attachments = raw.get("attachments", [])
        state = str(raw.get("state", "available")).lower()
        if attachments or state in ("in-use", "attached"):
            normalized_state = "attached"
        else:
            normalized_state = "unattached"

        size_gb = float(raw.get("size_gb", 0.0))
        used_gb = float(raw.get("storage_used_gb", 0.0))
        utilization_pct = round((used_gb / size_gb * 100.0), 1) if size_gb > 0 else 0.0

        return {
            "account_id": account_id,
            "provider": provider.lower(),
            "resource_id": str(raw.get("raw_id")),
            "name": raw.get("name") or raw.get("raw_id"),
            "resource_type": "block_storage",
            "region": raw.get("region", "global"),
            "environment_tag": env,
            "average_cpu": 0.0,
            "average_memory": 0.0,
            "monthly_cost": float(raw.get("monthly_cost", 0.0)),
            "last_activity": raw.get("create_time") or datetime.now(timezone.utc),
            "state": normalized_state,
            "tags": tags,
            "extra_metadata": {
                "size_gb": size_gb,
                "storage_used_gb": used_gb,
                "storage_utilization_pct": utilization_pct,
                "iops": int(raw.get("iops", 0)),
                "data_written_gb": float(raw.get("data_written_gb", 0.0)),
                "data_read_gb": float(raw.get("data_read_gb", 0.0)),
                "attachments_count": len(attachments),
                "is_unattached": (normalized_state == "unattached")
            }
        }

    @classmethod
    def normalize_ip(cls, raw: Dict[str, Any], provider: str, account_id: str) -> Dict[str, Any]:
        tags = raw.get("tags", {})
        env = cls.extract_environment(tags)
        
        is_assoc = raw.get("is_associated", False)
        normalized_state = "in-use" if is_assoc else "unassociated"

        return {
            "account_id": account_id,
            "provider": provider.lower(),
            "resource_id": str(raw.get("raw_id")),
            "name": raw.get("name") or raw.get("public_ip") or raw.get("raw_id"),
            "resource_type": "ip_address",
            "region": raw.get("region", "global"),
            "environment_tag": env,
            "average_cpu": 0.0,
            "average_memory": 0.0,
            "monthly_cost": float(raw.get("monthly_cost", 0.0)),
            "last_activity": datetime.now(timezone.utc),
            "state": normalized_state,
            "tags": tags,
            "extra_metadata": {
                "public_ip": raw.get("public_ip"),
                "is_associated": is_assoc,
                "bandwidth_mbps": int(raw.get("bandwidth_mbps", 0)),
                "data_transferred_gb": round(float(raw.get("data_transferred_gb", 0.0)), 2)
            }
        }
