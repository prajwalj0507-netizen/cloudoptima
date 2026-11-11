from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Account, AuditLog
from app.schemas import AccountCreate, AccountOut, AccountUpdate
from app.scheduler.pipeline import PipelineOrchestrator

router = APIRouter(prefix="/accounts", tags=["Cloud Accounts"])

@router.get("", response_model=List[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).all()

@router.post("", response_model=AccountOut)
def create_account(account_in: AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.account_id == account_in.account_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account with this ID already registered.")
    
    account = Account(**account_in.dict())
    db.add(account)
    db.add(AuditLog(
        event_type="ACCOUNT_REGISTERED",
        actor="admin",
        provider=account.provider,
        details={"account_id": account.account_id, "name": account.name}
    ))
    db.commit()
    db.refresh(account)
    return account

@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.patch("/{account_id}", response_model=AccountOut)
def update_account(account_id: str, update_in: AccountUpdate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    for field, val in update_in.dict(exclude_unset=True).items():
        setattr(account, field, val)

    db.add(AuditLog(
        event_type="ACCOUNT_UPDATED",
        actor="admin",
        provider=account.provider,
        details={"account_id": account.account_id, "updated_fields": update_in.dict(exclude_unset=True)}
    ))
    db.commit()
    db.refresh(account)
    return account

@router.post("/{account_id}/scan")
def trigger_account_scan(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    summary = PipelineOrchestrator.run_pipeline_for_account(db, account)
    return {"message": "Scan completed successfully", "results": summary}

@router.post("/scan-all")
def trigger_all_scans(db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.is_active == True).all()
    summaries = []
    for acc in accounts:
        try:
            summaries.append(PipelineOrchestrator.run_pipeline_for_account(db, acc))
        except Exception as e:
            summaries.append({"account_id": acc.account_id, "error": str(e)})
    return {"scanned_accounts": len(summaries), "details": summaries}
