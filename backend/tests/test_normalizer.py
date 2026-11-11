import pytest
from app.normalizer import CloudNormalizer

def test_environment_extraction():
    assert CloudNormalizer.extract_environment({"Environment": "production"}) == "production"
    assert CloudNormalizer.extract_environment({"env": "PROD-PRIMARY"}) == "production"
    assert CloudNormalizer.extract_environment({"Tier": "staging"}) == "staging"
    assert CloudNormalizer.extract_environment({"Stage": "test-env"}) == "test"
    assert CloudNormalizer.extract_environment({"Environment": "dev"}) == "dev"
    assert CloudNormalizer.extract_environment({}) == "unknown"

def test_normalize_instance():
    raw = {
        "raw_id": "i-12345",
        "name": "web-node",
        "instance_type": "t3.medium",
        "state": "running",
        "region": "us-east-1",
        "average_cpu": 4.5,
        "monthly_cost": 32.0,
        "tags": {"Environment": "dev"},
        "attached_to_lb": False
    }
    norm = CloudNormalizer.normalize_instance(raw, "aws", "acc-1")
    assert norm["resource_id"] == "i-12345"
    assert norm["resource_type"] == "compute_instance"
    assert norm["environment_tag"] == "dev"
    assert norm["state"] == "running"
    assert norm["average_cpu"] == 4.5
    assert norm["monthly_cost"] == 32.0

def test_normalize_unattached_volume():
    raw = {
        "raw_id": "vol-54321",
        "name": "scratch-disk",
        "size_gb": 100,
        "state": "available",
        "region": "us-west-2",
        "monthly_cost": 10.0,
        "attachments": [],
        "tags": {"Environment": "staging"}
    }
    norm = CloudNormalizer.normalize_volume(raw, "aws", "acc-1")
    assert norm["resource_id"] == "vol-54321"
    assert norm["state"] == "unattached"
    assert norm["extra_metadata"]["is_unattached"] is True
