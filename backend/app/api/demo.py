import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.database import get_db
from app.models import Account, Resource, Finding, RemediationAction, Approval, SavingsHistory, AuditLog
from app.scheduler.pipeline import PipelineOrchestrator

router = APIRouter(prefix="/demo", tags=["Demo Simulator & Seeder"])

@router.post("/seed")
def seed_demo_environment(db: Session = Depends(get_db)):
    """
    Seeds multi-cloud demo environment with realistic AWS, Azure, and GCP accounts,
    populates historical savings data, and runs an end-to-end detection & risk pipeline.
    """
    # 1. Register Accounts
    demo_accounts_data = [
        {
            "provider": "aws",
            "account_id": "aws-prod-01239",
            "name": "AWS Production & Analytics Account",
            "role_arn_or_creds": "arn:aws:iam::123456789012:role/CloudOptimaReadOnlyRole",
            "auto_remediate_low_risk": True,
            "is_active": True
        },
        {
            "provider": "azure",
            "account_id": "azure-sub-corp-981",
            "name": "Azure Enterprise Staging Subscription",
            "role_arn_or_creds": "/subscriptions/4f8b91a2-1100-azure-sp",
            "auto_remediate_low_risk": False,
            "is_active": True
        },
        {
            "provider": "gcp",
            "account_id": "gcp-proj-eng-441",
            "name": "GCP Engineering & Data Platform",
            "role_arn_or_creds": "projects/cloudoptima-eng/serviceAccounts/viewer-sa",
            "auto_remediate_low_risk": True,
            "is_active": True
        }
    ]

    accounts = []
    for acc_info in demo_accounts_data:
        acc = db.query(Account).filter(Account.account_id == acc_info["account_id"]).first()
        if not acc:
            acc = Account(**acc_info)
            db.add(acc)
            db.flush()
        accounts.append(acc)

    # 2. Seed 14-day Historical Savings Data for Charts
    today = date.today()
    for i in range(14, 0, -1):
        d = today - timedelta(days=i)
        for prov in ["aws", "azure", "gcp"]:
            existing = db.query(SavingsHistory).filter(SavingsHistory.date == d, SavingsHistory.provider == prov).first()
            if not existing:
                realized = round(random.uniform(25.0, 65.0) + (14 - i) * 12.0, 2)
                projected = round(random.uniform(150.0, 300.0), 2)
                db.add(SavingsHistory(
                    date=d,
                    provider=prov,
                    category="compute" if i % 2 == 0 else "storage",
                    realized_savings=realized,
                    projected_savings=projected
                ))

    db.commit()

    # 3. Trigger Pipeline Scan on all accounts
    scan_results = []
    for acc in accounts:
        res = PipelineOrchestrator.run_pipeline_for_account(db, acc)
        scan_results.append(res)

    return {
        "status": "success",
        "message": "Demo environment seeded and full multi-cloud pipeline executed successfully!",
        "seeded_accounts": len(accounts),
        "pipeline_scan_results": scan_results
    }

@router.post("/reset")
def reset_demo_environment(db: Session = Depends(get_db)):
    """Wipes all data to start fresh."""
    db.query(AuditLog).delete()
    db.query(SavingsHistory).delete()
    db.query(RemediationAction).delete()
    db.query(Approval).delete()
    db.query(Finding).delete()
    db.query(Resource).delete()
    db.query(Account).delete()
    db.commit()
    return {"status": "success", "message": "Demo environment reset. Database cleared."}
