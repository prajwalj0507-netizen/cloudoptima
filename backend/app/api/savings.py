from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from app.database import get_db
from app.models import Finding, RemediationAction, SavingsHistory, Approval
from app.schemas import SavingsSummaryOut, SavingsHistoryPoint

router = APIRouter(prefix="/savings", tags=["Savings & Analytics"])

@router.get("/summary", response_model=SavingsSummaryOut)
def get_savings_summary(db: Session = Depends(get_db)):
    # Open findings
    open_findings = db.query(Finding).filter(Finding.status.in_(["open", "pending_approval"])).all()
    remediated_findings = db.query(Finding).filter(Finding.status == "remediated").all()
    
    total_potential = sum(f.estimated_monthly_saving for f in open_findings)
    total_realized = sum(f.estimated_monthly_saving for f in remediated_findings)
    
    # By provider
    by_provider: Dict[str, float] = {}
    for f in open_findings:
        p = f.provider.lower()
        by_provider[p] = round(by_provider.get(p, 0.0) + f.estimated_monthly_saving, 2)
        
    # By category
    by_category: Dict[str, float] = {}
    for f in open_findings:
        c = f.category
        by_category[c] = round(by_category.get(c, 0.0) + f.estimated_monthly_saving, 2)

    # By risk level
    by_risk: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for f in open_findings:
        r = f.risk_level.upper()
        by_risk[r] = by_risk.get(r, 0) + 1

    return SavingsSummaryOut(
        total_potential_monthly_savings=round(total_potential, 2),
        total_realized_savings=round(total_realized, 2),
        open_findings_count=len(open_findings),
        remediated_count=len(remediated_findings),
        by_provider=by_provider,
        by_category=by_category,
        by_risk_level=by_risk
    )

@router.get("/history", response_model=List[SavingsHistoryPoint])
def get_savings_history(db: Session = Depends(get_db)):
    return db.query(SavingsHistory).order_by(SavingsHistory.date.asc()).all()

@router.post("/clear-realized")
def clear_realized_savings(db: Session = Depends(get_db)):
    """
    Clears confirmed realized savings by rolling back remediations and
    zeroing the realized savings ledger, allowing a fresh live demonstration.
    """
    remediations = db.query(RemediationAction).all()
    for r in remediations:
        r.status = "rolled_back"
    
    remediated = db.query(Finding).filter(Finding.status == "remediated").all()
    for f in remediated:
        f.status = "open"
        f.resolved_at = None
    
    histories = db.query(SavingsHistory).all()
    for h in histories:
        h.realized_savings = 0.0
    
    db.commit()
    return {"status": "success", "message": "Realized savings ledger successfully cleared to ₹0.00."}

@router.post("/reopen-all-waste")
def reopen_all_waste(db: Session = Depends(get_db)):
    """
    Re-opens all findings and approvals so the entire waste detection
    and remediation pipeline can be demonstrated from scratch.
    """
    findings = db.query(Finding).all()
    for f in findings:
        f.status = "open"
        f.resolved_at = None
    
    approvals = db.query(Approval).all()
    for a in approvals:
        a.status = "pending"
        a.decided_at = None
        
    db.commit()
    return {"status": "success", "message": "All waste findings and approvals successfully re-opened."}
