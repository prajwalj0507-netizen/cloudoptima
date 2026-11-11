import pytest
from app.detection import RuleEngine

def test_rule_unattached_volume():
    res = {
        "resource_id": "vol-orphan-01",
        "resource_type": "block_storage",
        "state": "unattached",
        "provider": "aws",
        "monthly_cost": 50.0,
        "extra_metadata": {"size_gb": 500, "is_unattached": True}
    }
    findings = RuleEngine.evaluate_resource(res)
    assert len(findings) == 1
    assert findings[0]["category"] == "unattached_volume"
    assert findings[0]["recommended_action"] == "delete_volume"
    assert findings[0]["estimated_monthly_saving"] >= 50.0

def test_rule_unused_ip():
    res = {
        "resource_id": "eip-unused-01",
        "resource_type": "ip_address",
        "state": "unassociated",
        "provider": "aws",
        "monthly_cost": 4.5,
        "extra_metadata": {"public_ip": "54.21.3.4", "is_associated": False}
    }
    findings = RuleEngine.evaluate_resource(res)
    assert len(findings) == 1
    assert findings[0]["category"] == "unused_ip"
    assert findings[0]["recommended_action"] == "release_ip"

def test_rule_idle_instance():
    res = {
        "resource_id": "i-idle-01",
        "name": "idle-worker",
        "resource_type": "compute_instance",
        "state": "running",
        "average_cpu": 3.2, # < 10%
        "provider": "aws",
        "monthly_cost": 200.0,
        "tags": {"Environment": "production"}
    }
    findings = RuleEngine.evaluate_resource(res)
    assert any(f["category"] == "idle_instance" for f in findings)
    f = next(f for f in findings if f["category"] == "idle_instance")
    assert f["recommended_action"] == "stop_instance"
    assert f["estimated_monthly_saving"] == 180.0

def test_rule_off_hours_dev():
    res = {
        "resource_id": "i-dev-01",
        "name": "dev-api",
        "resource_type": "compute_instance",
        "state": "running",
        "environment_tag": "dev",
        "average_cpu": 15.0,
        "provider": "aws",
        "monthly_cost": 100.0,
        "tags": {"Environment": "dev"}
    }
    findings = RuleEngine.evaluate_resource(res)
    assert any(f["category"] == "off_hours_dev" for f in findings)
    f = next(f for f in findings if f["category"] == "off_hours_dev")
    assert f["recommended_action"] == "schedule_stop"
    assert f["estimated_monthly_saving"] == 65.0
