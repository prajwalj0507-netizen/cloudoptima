from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models import Approval, Finding, Resource, RemediationAction, AuditLog
from app.schemas import ApprovalOut, ApprovalDecisionRequest, RemediationActionOut
from app.executor import RemediationExecutor, RemediationVerifier

router = APIRouter(prefix="/approvals", tags=["Human Approval Queue"])

@router.get("", response_model=List[ApprovalOut])
@router.get("/", response_model=List[ApprovalOut])
def list_approvals(
    status: Optional[str] = Query(None), # pending, approved, rejected
    db: Session = Depends(get_db)
):
    query = db.query(Approval)
    if status and isinstance(status, str):
        query = query.filter(Approval.status.ilike(status))
    
    approvals = query.order_by(Approval.created_at.desc()).all()
    results = []
    for app in approvals:
        finding = db.query(Finding).filter(Finding.id == app.finding_id).first()
        app_out = ApprovalOut.model_validate(app)
        if finding:
            app_out.finding = finding
        results.append(app_out)
    return results

@router.post("/{approval_id}/decision")
def decide_approval(
    approval_id: int,
    decision: ApprovalDecisionRequest,
    dry_run: bool = False,
    db: Session = Depends(get_db)
):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    finding = db.query(Finding).filter(Finding.id == approval.finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Associated finding not found")
    
    resource = db.query(Resource).filter(Resource.resource_id == finding.resource_id).first()
    if not resource:
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
            tags={"ManagedBy": "CloudOptima", "ApprovalId": str(approval_id)}
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)

    action_raw = decision.action or decision.decision or "approve"
    action_str = action_raw.lower()
    notes = decision.decision_notes or decision.notes or "Decided via CloudOptima Dashboard"
    approval.decided_at = datetime.now(timezone.utc)
    approval.decision_notes = notes
    approval.approver = "lead_engineer"

    if "approve" in action_str:
        approval.status = "approved"
        finding.status = "approved"
        
        # Create remediation action
        action = RemediationAction(
            finding_id=finding.id,
            resource_id=resource.resource_id,
            action_type=finding.recommended_action,
            status="approved",
            dry_run=dry_run,
            triggered_by="human_approver"
        )
        db.add(action)
        db.flush()

        db.add(AuditLog(
            event_type="APPROVAL_GRANTED",
            actor=approval.approver,
            resource_id=resource.resource_id,
            provider=finding.provider,
            details={"approval_id": approval_id, "notes": notes, "dry_run": dry_run}
        ))
        db.commit()

        # Execute & Verify
        RemediationExecutor.execute(db, action, finding, resource, dry_run=dry_run)
        RemediationVerifier.verify(db, action, finding, resource)

        return {
            "message": "Approval granted and remediation action executed",
            "approval_status": "approved",
            "remediation_status": action.status,
            "remediation_id": action.id,
            "snapshot_id": action.snapshot_id,
            "dry_run": dry_run
        }

    elif "reject" in action_str:
        approval.status = "rejected"
        finding.status = "dismissed"
        
        db.add(AuditLog(
            event_type="APPROVAL_REJECTED",
            actor=approval.approver,
            resource_id=resource.resource_id,
            provider=finding.provider,
            details={"approval_id": approval_id, "notes": notes}
        ))
        db.commit()
        return {
            "message": "Approval rejected. Action dismissed.",
            "approval_status": "rejected"
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")
