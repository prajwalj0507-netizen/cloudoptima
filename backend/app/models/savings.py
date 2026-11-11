from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from sqlalchemy.sql import func
from app.database import Base

class SavingsHistory(Base):
    __tablename__ = "savings_history"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True) # aws, azure, gcp, total
    category = Column(String(100), nullable=False, index=True) # compute, storage, network, ml_anomaly
    realized_savings = Column(Float, default=0.0) # actual confirmed savings
    projected_savings = Column(Float, default=0.0) # potential monthly savings
    currency = Column(String(10), default="INR")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
