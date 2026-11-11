import pytest
from app.detection import MLAnomalyDetector

def test_ml_anomaly_cost_spike():
    detector = MLAnomalyDetector()
    
    # 25 days of normal cost ~$50, then 5 days of sudden $220 spike
    cost_history = []
    for i in range(30, 0, -1):
        cost = 220.0 if i <= 3 else 50.0
        cost_history.append({
            "date": f"2026-10-{31 - i:02d}",
            "cost": cost,
            "currency": "INR"
        })

    findings = detector.detect_cost_spikes(cost_history, provider="aws", account_id="acc-aws-01")
    assert len(findings) > 0
    f = findings[0]
    assert f["detector_type"] == "ml_anomaly"
    assert f["category"] == "cost_spike"
    assert "Isolation Forest ML detected an abnormal cost spike" in f["reason"]
    assert f["estimated_monthly_saving"] > 0
