from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=False, index=True)
    resource_id = Column(String(200), nullable=False, index=True)
    action_type = Column(String(100), nullable=False) # delete_volume, stop_instance, release_ip, schedule_stop
    
    # Flags and State Machine
    # states: pending, approved, executing, executed, verifying, verified, rolling_back, rolled_back, failed
    status = Column(String(50), default="pending", index=True)
    dry_run = Column(Boolean, default=False)
    
    # Safety snapshot
    snapshot_id = Column(String(200), nullable=True) # e.g. snap-0123456789
    snapshot_metadata = Column(JSON, default=dict)
    
    # Audit & Verification details
    execution_result = Column(JSON, default=dict)
    verification_result = Column(JSON, default=dict)
    rollback_result = Column(JSON, default=dict)
    error_message = Column(String(500), nullable=True)
    
    triggered_by = Column(String(100), default="auto_remediator") # auto_remediator, or user email
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    rolled_back_at = Column(DateTime(timezone=True), nullable=True)
