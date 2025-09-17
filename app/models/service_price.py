"""
服务价格映射模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class ServicePrice(Base):
    """服务价格映射表"""
    __tablename__ = "service_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, nullable=False, unique=True, index=True)  # API服务ID
    service_name = Column(String(255), nullable=False)  # 服务名称
    api_price = Column(DECIMAL(10, 4), nullable=False)  # API价格（成本价）
    customer_price = Column(DECIMAL(10, 4), nullable=False)  # 客户价格（销售价）
    min_quantity = Column(Integer, default=1)  # 最小数量
    max_quantity = Column(Integer, default=10000)  # 最大数量
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "api_price": float(self.api_price),
            "customer_price": float(self.customer_price),
            "min_quantity": self.min_quantity,
            "max_quantity": self.max_quantity,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
