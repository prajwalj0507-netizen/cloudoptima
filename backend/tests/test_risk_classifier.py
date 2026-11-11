import pytest
from app.risk import RiskClassifier

def test_high_risk_production_load_balancer():
    finding = {"recommended_action": "stop_instance", "detector_type": "rule_engine"}
    resource = {
        "resource_id": "i-prod-01",
        "resource_type": "compute_instance",
        "environment_tag": "production",
        "average_cpu": 3.0,
        "extra_metadata": {"attached_to_lb": True}
    }
    result = RiskClassifier.evaluate(finding, resource)
    assert result["risk_level"] == "HIGH"
    assert result["risk_score"] >= 70.0
    assert result["requires_approval"] is True
    assert any("Application Load Balancer" in f["reason"] for f in result["factors"])

def test_low_risk_dev_unattached_volume():
    finding = {"recommended_action": "delete_volume", "detector_type": "rule_engine"}
    resource = {
        "resource_id": "vol-dev-01",
        "resource_type": "block_storage",
        "environment_tag": "dev",
        "state": "unattached",
        "extra_metadata": {"is_unattached": True, "attached_to_lb": False, "attachments_count": 0}
    }
    result = RiskClassifier.evaluate(finding, resource)
    # Dev (5) + Standalone (0) + Delete (20) - High Conf (-5) = 20 pts -> LOW
    assert result["risk_level"] == "LOW"
    assert result["risk_score"] < 35.0
    assert result["requires_approval"] is False

def test_medium_risk_staging_instance():
    finding = {"recommended_action": "stop_instance", "detector_type": "rule_engine"}
    resource = {
        "resource_id": "vm-stage-01",
        "resource_type": "compute_instance",
        "environment_tag": "staging",
        "average_cpu": 5.0,
        "extra_metadata": {"attached_to_lb": False, "attachments_count": 0}
    }
    result = RiskClassifier.evaluate(finding, resource)
    # Staging (20) + Standalone (10) + Stop (15) = 45 pts -> MEDIUM
    assert result["risk_level"] == "MEDIUM"
    assert 35.0 <= result["risk_score"] < 70.0
    assert result["requires_approval"] is True
