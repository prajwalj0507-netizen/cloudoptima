from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, index=True) # aws, azure, gcp
    account_id = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(150), nullable=False)
    role_arn_or_creds = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    auto_remediate_low_risk = Column(Boolean, default=False)
    last_scanned_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
