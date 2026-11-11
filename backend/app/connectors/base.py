from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class CloudConnectorBase(ABC):
    """
    Abstract Base Connector defining the unified Adapter interface for all cloud providers.
    All providers (AWS, Azure, GCP, and Mock/Simulator) implement this exact contract.
    Read-only collection by default; explicit safe mutating methods with snapshot and dry-run support.
    """

    def __init__(self, account_id: str, credentials_config: Optional[Dict[str, Any]] = None):
        self.account_id = account_id
        self.credentials_config = credentials_config or {}

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns provider identifier: 'aws', 'azure', or 'gcp'."""
        pass

    @abstractmethod
    def list_compute_instances(self) -> List[Dict[str, Any]]:
        """Discovers virtual compute instances, their status, tags, and attached networks/disks."""
        pass

    @abstractmethod
    def list_storage_volumes(self) -> List[Dict[str, Any]]:
        """Discovers block storage volumes, size, attachment status, and IO activity."""
        pass

    @abstractmethod
    def list_ip_addresses(self) -> List[Dict[str, Any]]:
        """Discovers public/static/elastic IP addresses and association state."""
        pass

    @abstractmethod
    def get_cost_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Returns daily spend trends for anomaly detection and cost reporting."""
        pass

    @abstractmethod
    def create_snapshot(self, resource_id: str) -> Dict[str, Any]:
        """Creates an immutable pre-action snapshot/backup before modification or deletion."""
        pass

    @abstractmethod
    def stop_instance(self, resource_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Stops an active compute instance safely."""
        pass

    @abstractmethod
    def start_instance(self, resource_id: str) -> Dict[str, Any]:
        """Starts an instance (used for rollback or manual restart)."""
        pass

    @abstractmethod
    def delete_volume(self, resource_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Deletes an unattached volume."""
        pass

    @abstractmethod
    def restore_snapshot(self, snapshot_id: str, original_resource_id: str) -> Dict[str, Any]:
        """Restores a volume from a pre-action snapshot during rollback."""
        pass

    @abstractmethod
    def release_ip(self, resource_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Releases an unassociated static/elastic IP."""
        pass

    @abstractmethod
    def verify_resource_state(self, resource_id: str, expected_state: str) -> Dict[str, Any]:
        """Verifies that the cloud provider reflects the target state post-action."""
        pass
