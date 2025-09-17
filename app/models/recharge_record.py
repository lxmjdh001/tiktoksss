"""
充值记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RechargeRecord(Base):
    """充值记录模型"""
    __tablename__ = "recharge_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(10, 4), nullable=False)
    payment_method = Column(String(50), nullable=False)
    status = Column(String(50), default="completed")
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    user = relationship("User", back_populates="recharge_records")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": float(self.amount),
            "payment_method": self.payment_method,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
