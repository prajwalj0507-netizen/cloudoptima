from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(100), ForeignKey("accounts.account_id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True) # aws, azure, gcp
    resource_id = Column(String(200), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=True)
    resource_type = Column(String(100), nullable=False, index=True) # compute_instance, block_storage, ip_address, database
    region = Column(String(100), nullable=False)
    environment_tag = Column(String(50), default="unknown", index=True) # production, staging, dev, sandbox
    average_cpu = Column(Float, default=0.0)
    average_memory = Column(Float, default=0.0)
    monthly_cost = Column(Float, default=0.0)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    state = Column(String(50), default="active", index=True) # running, stopped, unattached, available
    tags = Column(JSON, default=dict)
    extra_metadata = Column(JSON, default=dict) # e.g. attached_to, size_gb, instance_type
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
