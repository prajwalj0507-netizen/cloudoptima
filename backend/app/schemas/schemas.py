from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

# --- Account ---
class AccountBase(BaseModel):
    provider: str # aws, azure, gcp
    account_id: str
    name: str
    role_arn_or_creds: Optional[str] = None
    is_active: bool = True
    auto_remediate_low_risk: bool = False

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    role_arn_or_creds: Optional[str] = None
    is_active: Optional[bool] = None
    auto_remediate_low_risk: Optional[bool] = None

class AccountOut(AccountBase):
    id: int
    last_scanned_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Resource ---
class ResourceOut(BaseModel):
    id: int
    account_id: str
    provider: str
    resource_id: str
    name: Optional[str]
    resource_type: str
    region: str
    environment_tag: str
    average_cpu: float
    average_memory: float
    monthly_cost: float
    last_activity: Optional[datetime]
    state: str
    tags: Dict[str, Any] = {}
    extra_metadata: Dict[str, Any] = {}
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# --- Risk ---
class RiskFactorDetail(BaseModel):
    factor_name: str
    points: float
    weight_pct: float
    reason: str

class RiskAssessment(BaseModel):
    risk_score: float # 0 to 100
    risk_level: str # LOW, MEDIUM, HIGH
    factors: List[RiskFactorDetail]
    requires_approval: bool
    summary: str

# --- Finding ---
class FindingOut(BaseModel):
    id: int
    resource_id: str
    provider: str
    detector_type: str
    category: str
    reason: str
    recommended_action: str
    estimated_monthly_saving: float
    risk_score: float
    risk_level: str
    risk_breakdown: Dict[str, Any] = {}
    status: str
    detected_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resource: Optional[ResourceOut] = None

    model_config = ConfigDict(from_attributes=True)

# --- Approval ---
class ApprovalOut(BaseModel):
    id: int
    finding_id: int
    status: str
    requested_by: str
    approver: Optional[str]
    decision_notes: Optional[str]
    created_at: Optional[datetime]
    decided_at: Optional[datetime]
    finding: Optional[FindingOut] = None

    model_config = ConfigDict(from_attributes=True)

class ApprovalDecisionRequest(BaseModel):
    action: Optional[str] = None # "approve" or "reject"
    decision: Optional[str] = None # alternative alias
    decision_notes: Optional[str] = "Approved via CloudOptima Dashboard"
    notes: Optional[str] = None # alternative alias

# --- Remediation ---
class RemediationTriggerRequest(BaseModel):
    finding_id: int
    dry_run: bool = False

class RemediationActionOut(BaseModel):
    id: int
    finding_id: int
    resource_id: str
    action_type: str
    status: str
    dry_run: bool
    snapshot_id: Optional[str]
    snapshot_metadata: Dict[str, Any] = {}
    execution_result: Dict[str, Any] = {}
    verification_result: Dict[str, Any] = {}
    rollback_result: Dict[str, Any] = {}
    error_message: Optional[str]
    triggered_by: str
    created_at: Optional[datetime]
    executed_at: Optional[datetime]
    verified_at: Optional[datetime]
    rolled_back_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class RollbackRequest(BaseModel):
    remediation_id: int
    reason: Optional[str] = "Manual rollback requested"

# --- Savings & Analytics ---
class SavingsSummaryOut(BaseModel):
    total_potential_monthly_savings: float
    total_realized_savings: float
    open_findings_count: int
    remediated_count: int
    by_provider: Dict[str, float]
    by_category: Dict[str, float]
    by_risk_level: Dict[str, int]
    currency: str = "INR"
    currency_symbol: str = "₹"

class SavingsHistoryPoint(BaseModel):
    date: date
    provider: str
    category: str
    realized_savings: float
    projected_savings: float
    currency: str = "INR"

    model_config = ConfigDict(from_attributes=True)

# --- Audit Log ---
class AuditLogOut(BaseModel):
    id: int
    event_type: str
    actor: str
    resource_id: Optional[str]
    provider: Optional[str]
    details: Dict[str, Any] = {}
    ip_address: Optional[str]
    timestamp: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# --- Full Dashboard Stats ---
class DashboardOverview(BaseModel):
    savings_summary: SavingsSummaryOut
    recent_findings: List[FindingOut]
    pending_approvals: List[ApprovalOut]
    recent_remediations: List[RemediationActionOut]
    recent_audits: List[AuditLogOut]
