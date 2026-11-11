from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(200), ForeignKey("resources.resource_id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    detector_type = Column(String(50), nullable=False) # rule_engine, ml_anomaly
    category = Column(String(100), nullable=False, index=True) # unattached_volume, unused_ip, idle_instance, off_hours_dev, cost_spike
    reason = Column(String(500), nullable=False) # Plain-language explanation
    recommended_action = Column(String(100), nullable=False) # delete_volume, release_ip, stop_instance, schedule_stop
    estimated_monthly_saving = Column(Float, default=0.0)
    
    # Risk decision
    risk_score = Column(Float, default=0.0) # 0 to 100
    risk_level = Column(String(20), default="MEDIUM", index=True) # LOW, MEDIUM, HIGH
    risk_breakdown = Column(JSON, default=dict)
    
    status = Column(String(50), default="open", index=True) # open, pending_approval, approved, remediating, remediated, dismissed
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
