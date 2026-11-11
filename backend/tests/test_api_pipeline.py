import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)

def setup_module():
    init_db()

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_demo_seed_and_pipeline_flow():
    # 1. Trigger Seed
    seed_res = client.post("/api/demo/seed")
    assert seed_res.status_code == 200
    data = seed_res.json()
    assert data["status"] == "success"
    assert data["seeded_accounts"] == 3

    # 2. Check Savings Summary
    summary_res = client.get("/api/savings/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["open_findings_count"] > 0
    assert summary["total_potential_monthly_savings"] > 0

    # 3. Check Findings
    findings_res = client.get("/api/findings")
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) > 0

    # 4. Check Approval Queue
    approvals_res = client.get("/api/approvals?status=pending")
    assert approvals_res.status_code == 200
    approvals = approvals_res.json()
    assert len(approvals) > 0

    # 5. Approve one pending action with pre-action snapshot
    app_id = approvals[0]["id"]
    decision_res = client.post(f"/api/approvals/{app_id}/decision?dry_run=false", json={
        "action": "approve",
        "decision_notes": "Approved in pytest pipeline suite"
    })
    assert decision_res.status_code == 200
    dec_data = decision_res.json()
    assert dec_data["approval_status"] == "approved"
    assert dec_data["remediation_status"] == "verified"
    assert "snapshot_id" in dec_data

    # 6. Audit Trail check
    audit_res = client.get("/api/audit")
    assert audit_res.status_code == 200
    audits = audit_res.json()
    assert len(audits) > 0
    assert any(a["event_type"] == "APPROVAL_GRANTED" for a in audits)


def test_auth_admin_and_approver_logins():
    # 1. Admin login
    admin_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_res.status_code == 200
    admin_data = admin_res.json()
    assert admin_data["user"]["role"] == "admin"
    assert admin_data["user"]["username"] == "admin"
    assert "access_token" in admin_data
    token = admin_data["access_token"]

    # 2. Verify token via /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"
    assert me_res.json()["role"] == "admin"

    # 3. Approver login
    approver_res = client.post("/api/auth/login", json={"username": "approver", "password": "approver123"})
    assert approver_res.status_code == 200
    approver_data = approver_res.json()
    assert approver_data["user"]["role"] == "approver"
    assert approver_data["user"]["username"] == "approver"
    assert "access_token" in approver_data

    # 4. Invalid credentials
    bad_res = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert bad_res.status_code == 401


