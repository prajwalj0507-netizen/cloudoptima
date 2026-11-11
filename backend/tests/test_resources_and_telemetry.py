import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)

def setup_module():
    init_db()
    # Seed demo environment to guarantee resources exist
    client.post("/api/demo/seed")

def test_list_resources():
    res = client.get("/api/resources")
    assert res.status_code == 200
    resources = res.json()
    assert len(resources) > 0

    # Verify hardware specs and data usage fields exist in extra_metadata
    compute_found = False
    storage_found = False
    ip_found = False

    for r in resources:
        meta = r.get("extra_metadata", {})
        if r["resource_type"] == "compute_instance":
            compute_found = True
            assert "vcpus" in meta
            assert "memory_gb" in meta
            assert "network_in_gb" in meta
            assert "network_out_gb" in meta
            assert "data_transfer_gb" in meta
        elif r["resource_type"] == "block_storage":
            storage_found = True
            assert "size_gb" in meta
            assert "storage_used_gb" in meta
            assert "storage_utilization_pct" in meta
        elif r["resource_type"] == "ip_address":
            ip_found = True
            assert "data_transferred_gb" in meta

    assert compute_found
    assert storage_found
    assert ip_found

def test_list_resources_filtering():
    # Filter by provider
    aws_res = client.get("/api/resources?provider=aws")
    assert aws_res.status_code == 200
    for r in aws_res.json():
        assert r["provider"] == "aws"

    # Filter by resource type
    comp_res = client.get("/api/resources?resource_type=compute_instance")
    assert comp_res.status_code == 200
    for r in comp_res.json():
        assert r["resource_type"] == "compute_instance"

def test_resource_telemetry_summary():
    res = client.get("/api/resources/telemetry/summary")
    assert res.status_code == 200
    data = res.json()

    assert data["total_resources"] > 0
    assert data["total_vcpus"] > 0
    assert data["total_memory_gb"] > 0
    assert data["total_storage_provisioned_gb"] > 0
    assert data["total_storage_used_gb"] > 0
    assert data["storage_utilization_pct"] > 0
    assert data["total_network_out_gb"] > 0
    assert data["total_data_transfer_gb"] > 0
    assert data["currency_symbol"] == "₹"

    # Provider breakdown verification
    assert "aws" in data["by_provider"]
    assert "azure" in data["by_provider"]
    assert "gcp" in data["by_provider"]
    assert data["by_provider"]["aws"]["count"] > 0
    assert data["by_provider"]["aws"]["storage_gb"] > 0
    assert data["by_provider"]["aws"]["data_transfer_gb"] > 0
