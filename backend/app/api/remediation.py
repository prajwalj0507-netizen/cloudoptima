from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models import RemediationAction, Finding, Resource, AuditLog, Approval
from app.schemas import RemediationActionOut, RemediationTriggerRequest, RollbackRequest
from app.executor import RemediationExecutor, RemediationVerifier, RollbackManager

router = APIRouter(tags=["Remediation & Execution"])

@router.get("/remediation", response_model=List[RemediationActionOut])
@router.get("/remediation/", response_model=List[RemediationActionOut])
@router.get("/remediations", response_model=List[RemediationActionOut])
@router.get("/remediations/", response_model=List[RemediationActionOut])
def list_remediations(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(RemediationAction)
    if status and isinstance(status, str):
        query = query.filter(RemediationAction.status.ilike(status))
    return query.order_by(RemediationAction.created_at.desc()).all()

@router.post("/remediation/trigger", response_model=RemediationActionOut)
@router.post("/remediation/execute", response_model=RemediationActionOut)
@router.post("/remediations/trigger", response_model=RemediationActionOut)
@router.post("/remediations/execute", response_model=RemediationActionOut)
def trigger_remediation(
    req: RemediationTriggerRequest,
    db: Session = Depends(get_db)
):
    finding = db.query(Finding).filter(Finding.id == req.finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    resource = db.query(Resource).filter(Resource.resource_id == finding.resource_id).first()
    if not resource:
        # Create tracking resource record for anomalies or un-cataloged findings
        resource = Resource(
            account_id="acc-" + (finding.provider or "cloud"),
            provider=finding.provider or "aws",
            resource_id=finding.resource_id,
            name=f"{finding.provider.upper() if finding.provider else 'Cloud'} Workload ({finding.resource_id})",
            resource_type="cost_anomaly_target" if "anomaly" in str(finding.resource_id) else "compute_instance",
            region="global",
            environment_tag="production",
            average_cpu=0.0,
            average_memory=0.0,
            monthly_cost=finding.estimated_monthly_saving or 100.0,
            state="active",
            tags={"ManagedBy": "CloudOptima", "FindingId": str(finding.id)}
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)
    
    action = RemediationAction(
        finding_id=finding.id,
        resource_id=resource.resource_id,
        action_type=finding.recommended_action,
        status="approved",
        dry_run=req.dry_run,
        triggered_by="operator"
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    # Execute and Verify
    RemediationExecutor.execute(db, action, finding, resource, dry_run=req.dry_run)
    RemediationVerifier.verify(db, action, finding, resource)
    
    # Synchronize approval queue if pending approval existed for this finding
    approval = db.query(Approval).filter(Approval.finding_id == finding.id).first()
    if approval and approval.status == "pending":
        approval.status = "approved"
        approval.decided_at = datetime.now(timezone.utc)
        approval.approver = "operator"
        approval.decision_notes = "Direct execution via waste findings portal"
        db.commit()

    db.refresh(action)
    return action

@router.post("/remediation/rollback")
@router.post("/remediations/rollback")
def rollback_remediation(
    req: RollbackRequest,
    db: Session = Depends(get_db)
):
    action = db.query(RemediationAction).filter(RemediationAction.id == req.remediation_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Remediation action not found")
    
    finding = db.query(Finding).filter(Finding.id == action.finding_id).first()
    resource = db.query(Resource).filter(Resource.resource_id == action.resource_id).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Target resource not found")

    RollbackManager.rollback(
        db=db,
        action=action,
        finding=finding,
        resource=resource,
        reason=req.reason
    )

    return {
        "message": f"Rollback completed for action {action.id}",
        "action_id": action.id,
        "status": action.status,
        "rollback_result": action.rollback_result
    }
