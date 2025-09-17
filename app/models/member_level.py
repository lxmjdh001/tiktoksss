"""
会员等级模型
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL
from sqlalchemy.sql import func
from app.database import Base

class MemberLevel(Base):
    """会员等级模型"""
    __tablename__ = "member_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    min_consumption = Column(DECIMAL(10, 2), default=0.00)
    cashback_rate = Column(DECIMAL(5, 4), default=0.0000)
    max_orders = Column(Integer, default=1000)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "min_consumption": float(self.min_consumption),
            "cashback_rate": float(self.cashback_rate),
            "max_orders": self.max_orders,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
