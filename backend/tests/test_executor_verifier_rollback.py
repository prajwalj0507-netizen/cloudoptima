import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Account, Resource, Finding, RemediationAction, AuditLog, SavingsHistory
from app.executor import RemediationExecutor, RemediationVerifier, RollbackManager

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_dry_run_execution(db_session):
    account = Account(provider="aws", account_id="acc-test-dry", name="Test Account")
    db_session.add(account)
    resource = Resource(
        account_id="acc-test-dry", provider="aws", resource_id="vol-test-dry",
        resource_type="block_storage", region="us-east-1", state="unattached", monthly_cost=50.0
    )
    db_session.add(resource)
    finding = Finding(
        resource_id="vol-test-dry", provider="aws", detector_type="rule_engine",
        category="unattached_volume", reason="Idle volume", recommended_action="delete_volume",
        estimated_monthly_saving=50.0, risk_score=20.0, risk_level="LOW"
    )
    db_session.add(finding)
    db_session.commit()

    action = RemediationAction(
        finding_id=finding.id, resource_id=resource.resource_id,
        action_type="delete_volume", status="approved", dry_run=True
    )
    db_session.add(action)
    db_session.commit()

    # Execute dry-run
    RemediationExecutor.execute(db_session, action, finding, resource, dry_run=True)
    assert action.status == "executed"
    assert action.execution_result.get("dry_run") is True
    assert resource.state == "unattached" # Not deleted in dry-run!

def test_snapshot_creation_and_execution_and_verifier(db_session):
    account = Account(provider="aws", account_id="acc-live-test", name="Live Account")
    db_session.add(account)
    resource = Resource(
        account_id="acc-live-test", provider="aws", resource_id="vol-0941bc4e27f10",
        resource_type="block_storage", region="us-east-1", state="unattached", monthly_cost=50.0
    )
    db_session.add(resource)
    finding = Finding(
        resource_id="vol-0941bc4e27f10", provider="aws", detector_type="rule_engine",
        category="unattached_volume", reason="Idle volume", recommended_action="delete_volume",
        estimated_monthly_saving=50.0, risk_score=20.0, risk_level="LOW"
    )
    db_session.add(finding)
    db_session.commit()

    action = RemediationAction(
        finding_id=finding.id, resource_id=resource.resource_id,
        action_type="delete_volume", status="approved", dry_run=False
    )
    db_session.add(action)
    db_session.commit()

    # Execute
    RemediationExecutor.execute(db_session, action, finding, resource, dry_run=False)
    assert action.status == "executed"
    assert action.snapshot_id is not None # Snapshot taken!
    assert "snap-aws-" in action.snapshot_id

    # Verify
    RemediationVerifier.verify(db_session, action, finding, resource)
    assert action.status == "verified"
    assert finding.status == "remediated"
    assert resource.state == "deleted"

    # Rollback
    RollbackManager.rollback(db_session, action, finding, resource, reason="Guide demonstration test")
    assert action.status == "rolled_back"
    assert resource.state == "available" # Restored from snapshot!
    assert finding.status == "open"
