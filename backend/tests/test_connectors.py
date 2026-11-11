import pytest
from app.connectors import get_connector, MockMultiCloudConnector

def test_mock_multi_cloud_connectors():
    for prov in ["aws", "azure", "gcp"]:
        conn = get_connector(provider=prov, account_id=f"test-{prov}", force_mock=True)
        assert conn.provider_name == prov
        
        # Test listing
        instances = conn.list_compute_instances()
        volumes = conn.list_storage_volumes()
        ips = conn.list_ip_addresses()
        cost_hist = conn.get_cost_history(days=30)
        
        assert isinstance(instances, list)
        assert isinstance(volumes, list)
        assert isinstance(ips, list)
        assert len(cost_hist) == 30

def test_connector_actions_and_snapshots():
    conn = MockMultiCloudConnector(account_id="test-aws", provider="aws")
    
    # Snapshot creation
    snap = conn.create_snapshot("vol-0941bc4e27f10")
    assert "snapshot_id" in snap
    assert snap["status"] == "completed"
    
    # Stop instance
    stop_res = conn.stop_instance("i-0a8174fbcd738")
    assert stop_res["success"] is True
    assert stop_res["new_state"] == "stopped"
    
    # Verify state
    verif = conn.verify_resource_state("i-0a8174fbcd738", "stopped")
    assert verif["verified"] is True

    # Restore / Start
    start_res = conn.start_instance("i-0a8174fbcd738")
    assert start_res["success"] is True
    assert start_res["new_state"] == "running"
