import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from app.connectors.base import CloudConnectorBase

class MockMultiCloudConnector(CloudConnectorBase):
    """
    High-fidelity Multi-Cloud Simulator for AWS, Azure, and GCP.
    Enables immediate testing and guide presentation without cloud accounts or fees.
    Maintains simulated in-memory cloud state across remediation, snapshots, and rollbacks.
    """

    def __init__(self, account_id: str, provider: str = "aws", credentials_config: Optional[Dict[str, Any]] = None):
        super().__init__(account_id, credentials_config)
        self._provider = provider
        self._simulated_state: Dict[str, Dict[str, Any]] = {}
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._init_mock_catalog()

    @property
    def provider_name(self) -> str:
        return self._provider

    def _init_mock_catalog(self):
        now = datetime.now(timezone.utc)
        
        if self._provider == "aws":
            self.instances = [
                {
                    "raw_id": "i-0a8174fbcd738",
                    "name": "analytics-worker-node-02",
                    "instance_type": "c5.2xlarge",
                    "state": "running",
                    "region": "us-east-1",
                    "environment": "dev",
                    "vcpus": 8,
                    "memory_gb": 16,
                    "average_cpu": 3.4, # < 10% CPU for 7 days (Idle waste)
                    "average_memory": 14.2,
                    "network_in_gb": 34.2,
                    "network_out_gb": 112.8,
                    "data_transfer_gb": 147.0,
                    "monthly_cost": 248.00,
                    "attached_to_lb": False,
                    "tags": {"Environment": "dev", "Project": "Analytics", "Owner": "DataTeam"}
                },
                {
                    "raw_id": "i-091fb72ca410b",
                    "name": "payments-core-prod-01",
                    "instance_type": "m5.2xlarge",
                    "state": "running",
                    "region": "us-east-1",
                    "environment": "production",
                    "vcpus": 8,
                    "memory_gb": 32,
                    "average_cpu": 6.8, # Prod instance with low CPU -> High Risk approval test
                    "average_memory": 22.0,
                    "network_in_gb": 185.0,
                    "network_out_gb": 640.5,
                    "data_transfer_gb": 825.5,
                    "monthly_cost": 280.00,
                    "attached_to_lb": True,
                    "tags": {"Environment": "production", "Service": "Payments", "Criticality": "Tier-1"}
                },
                {
                    "raw_id": "i-057d38ae9123c",
                    "name": "qa-test-env-backend",
                    "instance_type": "t3.xlarge",
                    "state": "running",
                    "region": "us-west-2",
                    "environment": "test",
                    "vcpus": 4,
                    "memory_gb": 16,
                    "average_cpu": 15.0, # Active non-prod running 24/7 outside working hours
                    "average_memory": 35.0,
                    "network_in_gb": 28.5,
                    "network_out_gb": 76.2,
                    "data_transfer_gb": 104.7,
                    "monthly_cost": 125.00,
                    "attached_to_lb": False,
                    "tags": {"Environment": "test", "Schedule": "none", "AutoOff": "false"}
                }
            ]
            self.volumes = [
                {
                    "raw_id": "vol-0941bc4e27f10",
                    "name": "abandoned-postgres-scratch-vol",
                    "size_gb": 500,
                    "storage_used_gb": 38.0,
                    "iops": 0,
                    "data_written_gb": 0.0,
                    "data_read_gb": 0.0,
                    "state": "available", # Unattached EBS
                    "region": "us-east-1",
                    "environment": "dev",
                    "monthly_cost": 50.00,
                    "attachments": [],
                    "tags": {"Environment": "dev", "Orphaned": "true"}
                },
                {
                    "raw_id": "vol-0182a4d9ef332",
                    "name": "prod-customer-db-primary",
                    "size_gb": 1000,
                    "storage_used_gb": 820.0,
                    "iops": 3200,
                    "data_written_gb": 420.0,
                    "data_read_gb": 1840.0,
                    "state": "in-use",
                    "region": "us-east-1",
                    "environment": "production",
                    "monthly_cost": 120.00,
                    "attachments": [{"InstanceId": "i-091fb72ca410b"}],
                    "tags": {"Environment": "production"}
                }
            ]
            self.ips = [
                {
                    "raw_id": "eipalloc-01783abf32",
                    "public_ip": "54.210.14.92",
                    "name": "legacy-nat-gateway-ip",
                    "is_associated": False, # Unused Elastic IP
                    "state": "unassociated",
                    "region": "us-east-1",
                    "environment": "dev",
                    "bandwidth_mbps": 0,
                    "data_transferred_gb": 0.0,
                    "monthly_cost": 4.50,
                    "tags": {"Environment": "dev"}
                }
            ]

        elif self._provider == "azure":
            self.instances = [
                {
                    "raw_id": "vm-batch-indexer-stg",
                    "name": "vm-batch-indexer-stg",
                    "instance_type": "Standard_D4s_v5",
                    "state": "running",
                    "region": "eastus2",
                    "environment": "staging",
                    "vcpus": 4,
                    "memory_gb": 16,
                    "average_cpu": 2.8, # Idle instance
                    "average_memory": 18.0,
                    "network_in_gb": 19.4,
                    "network_out_gb": 58.6,
                    "data_transfer_gb": 78.0,
                    "monthly_cost": 145.00,
                    "attached_to_lb": False,
                    "tags": {"Environment": "staging", "CostCenter": "CC-902"}
                }
            ]
            self.volumes = [
                {
                    "raw_id": "disk-data-stage-backup",
                    "name": "disk-data-stage-backup",
                    "size_gb": 1024,
                    "storage_used_gb": 185.0,
                    "iops": 0,
                    "data_written_gb": 0.0,
                    "data_read_gb": 0.0,
                    "state": "unattached", # Unattached Managed Disk
                    "region": "eastus2",
                    "environment": "staging",
                    "monthly_cost": 138.00,
                    "attachments": [],
                    "tags": {"Environment": "staging"}
                }
            ]
            self.ips = [
                {
                    "raw_id": "pip-gateway-idle-01",
                    "public_ip": "20.128.45.19",
                    "name": "pip-gateway-idle-01",
                    "is_associated": False,
                    "state": "unassociated",
                    "region": "eastus2",
                    "environment": "staging",
                    "bandwidth_mbps": 0,
                    "data_transferred_gb": 0.0,
                    "monthly_cost": 3.80,
                    "tags": {"Environment": "staging"}
                }
            ]

        else: # GCP
            self.instances = [
                {
                    "raw_id": "gcp-vm-dev-microservices",
                    "name": "gcp-vm-dev-microservices",
                    "instance_type": "e2-standard-4",
                    "state": "RUNNING",
                    "region": "us-central1",
                    "environment": "dev",
                    "vcpus": 4,
                    "memory_gb": 16,
                    "average_cpu": 12.0, # Dev VM running 24/7 off-hours
                    "average_memory": 28.0,
                    "network_in_gb": 42.1,
                    "network_out_gb": 94.3,
                    "data_transfer_gb": 136.4,
                    "monthly_cost": 98.00,
                    "attached_to_lb": False,
                    "tags": {"Environment": "dev", "Department": "Engineering"}
                }
            ]
            self.volumes = [
                {
                    "raw_id": "disk-gcp-ml-scratch",
                    "name": "disk-gcp-ml-scratch",
                    "size_gb": 300,
                    "storage_used_gb": 14.0,
                    "iops": 0,
                    "data_written_gb": 0.0,
                    "data_read_gb": 0.0,
                    "state": "UNATTACHED", # Unattached GCP Disk
                    "region": "us-central1",
                    "environment": "dev",
                    "monthly_cost": 42.00,
                    "attachments": [],
                    "tags": {"Environment": "dev"}
                }
            ]
            self.ips = []

    def list_compute_instances(self) -> List[Dict[str, Any]]:
        # Return state taking into account any local stop actions
        result = []
        for inst in self.instances:
            item = dict(inst)
            if item["raw_id"] in self._simulated_state:
                item["state"] = self._simulated_state[item["raw_id"]].get("state", item["state"])
            result.append(item)
        return result

    def list_storage_volumes(self) -> List[Dict[str, Any]]:
        result = []
        for vol in self.volumes:
            if vol["raw_id"] in self._simulated_state and self._simulated_state[vol["raw_id"]].get("deleted", False):
                continue
            result.append(dict(vol))
        return result

    def list_ip_addresses(self) -> List[Dict[str, Any]]:
        result = []
        for ip in self.ips:
            if ip["raw_id"] in self._simulated_state and self._simulated_state[ip["raw_id"]].get("released", False):
                continue
            result.append(dict(ip))
        return result

    def get_cost_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Generates realistic 30-day cost history with a notable recent cost spike
        to trigger and demonstrate the ML Isolation Forest Anomaly Detector.
        """
        history = []
        now = datetime.now(timezone.utc)
        base_cost = 40.0 if self._provider == "aws" else (25.0 if self._provider == "azure" else 18.0)
        
        for i in range(days, 0, -1):
            date_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            # Spike spend in the last 3 days by 3.5x
            if i <= 3:
                cost = round(base_cost * 3.6 + random.uniform(5.0, 15.0), 2)
            else:
                cost = round(base_cost + random.uniform(-3.0, 3.0), 2)
            
            history.append({
                "date": date_str,
                "cost": max(cost, 1.0),
                "currency": "INR"
            })
        return history

    def create_snapshot(self, resource_id: str) -> Dict[str, Any]:
        snapshot_id = f"snap-{self._provider}-{int(datetime.now().timestamp())}-{random.randint(100, 999)}"
        snapshot_data = {
            "snapshot_id": snapshot_id,
            "resource_id": resource_id,
            "provider": self._provider,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._snapshots[snapshot_id] = snapshot_data
        return snapshot_data

    def stop_instance(self, resource_id: str, dry_run: bool = False) -> Dict[str, Any]:
        if dry_run:
            return {"action": "stop_instance", "resource_id": resource_id, "dry_run": True, "success": True}
        
        self._simulated_state[resource_id] = {"state": "stopped"}
        return {"action": "stop_instance", "resource_id": resource_id, "success": True, "new_state": "stopped"}

    def start_instance(self, resource_id: str) -> Dict[str, Any]:
        self._simulated_state[resource_id] = {"state": "running"}
        return {"action": "start_instance", "resource_id": resource_id, "success": True, "new_state": "running"}

    def delete_volume(self, resource_id: str, dry_run: bool = False) -> Dict[str, Any]:
        if dry_run:
            return {"action": "delete_volume", "resource_id": resource_id, "dry_run": True, "success": True}
        
        self._simulated_state[resource_id] = {"deleted": True, "state": "deleted"}
        return {"action": "delete_volume", "resource_id": resource_id, "success": True, "new_state": "deleted"}

    def restore_snapshot(self, snapshot_id: str, original_resource_id: str) -> Dict[str, Any]:
        restored_id = f"vol-restored-{int(datetime.now().timestamp())}"
        if original_resource_id in self._simulated_state:
            self._simulated_state[original_resource_id] = {"deleted": False, "state": "available"}
        return {
            "action": "restore_snapshot",
            "snapshot_id": snapshot_id,
            "restored_resource_id": restored_id,
            "success": True
        }

    def release_ip(self, resource_id: str, dry_run: bool = False) -> Dict[str, Any]:
        if dry_run:
            return {"action": "release_ip", "resource_id": resource_id, "dry_run": True, "success": True}
        
        self._simulated_state[resource_id] = {"released": True, "state": "released"}
        return {"action": "release_ip", "resource_id": resource_id, "success": True, "new_state": "released"}

    def verify_resource_state(self, resource_id: str, expected_state: str) -> Dict[str, Any]:
        current = self._simulated_state.get(resource_id, {}).get("state", expected_state)
        verified = (current == expected_state or (expected_state == "deleted" and self._simulated_state.get(resource_id, {}).get("deleted", False)))
        return {
            "resource_id": resource_id,
            "verified": verified,
            "current_state": current,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
