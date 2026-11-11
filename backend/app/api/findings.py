from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Finding, Resource, AuditLog
from app.schemas import FindingOut

router = APIRouter(prefix="/findings", tags=["Waste Findings"])

@router.get("", response_model=List[FindingOut])
@router.get("/", response_model=List[FindingOut])
def list_findings(
    provider: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Finding)
    if provider and isinstance(provider, str):
        query = query.filter(Finding.provider == provider.lower())
    if risk_level and isinstance(risk_level, str):
        query = query.filter(Finding.risk_level == risk_level.upper())
    if status and isinstance(status, str):
        query = query.filter(Finding.status == status)
    if category and isinstance(category, str):
        query = query.filter(Finding.category == category)
    
    findings = query.order_by(Finding.risk_score.desc(), Finding.estimated_monthly_saving.desc()).all()
    
    # Attach resource details
    results = []
    for f in findings:
        res = db.query(Resource).filter(Resource.resource_id == f.resource_id).first()
        f_out = FindingOut.model_validate(f)
        f_out.resource = res
        results.append(f_out)
    return results

@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    res = db.query(Resource).filter(Resource.resource_id == finding.resource_id).first()
    f_out = FindingOut.model_validate(finding)
    f_out.resource = res
    return f_out

@router.post("/{finding_id}/dismiss")
def dismiss_finding(finding_id: int, reason: str = "Accepted business risk", db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    finding.status = "dismissed"
    db.add(AuditLog(
        event_type="FINDING_DISMISSED",
        actor="user",
        resource_id=finding.resource_id,
        provider=finding.provider,
        details={"finding_id": finding_id, "reason": reason}
    ))
    db.commit()
    return {"message": "Finding dismissed successfully", "id": finding_id}
