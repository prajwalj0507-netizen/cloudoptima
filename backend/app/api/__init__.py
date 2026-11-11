from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.accounts import router as accounts_router
from app.api.findings import router as findings_router
from app.api.approvals import router as approvals_router
from app.api.remediation import router as remediation_router
from app.api.savings import router as savings_router
from app.api.audit import router as audit_router
from app.api.demo import router as demo_router
from app.api.resources import router as resources_router
from app.api.focus_datasets import router as focus_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(accounts_router)
api_router.include_router(resources_router)
api_router.include_router(focus_router)
api_router.include_router(findings_router)
api_router.include_router(approvals_router)
api_router.include_router(remediation_router)
api_router.include_router(savings_router)
api_router.include_router(audit_router)
api_router.include_router(demo_router)

__all__ = ["api_router"]
