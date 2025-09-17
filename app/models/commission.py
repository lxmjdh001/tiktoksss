"""
返佣相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class CommissionRecord(Base):
    """返佣记录模型"""
    __tablename__ = "commission_records"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 代理ID
    consumer_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 消费者ID
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)  # 订单ID
    commission_type = Column(String(20), nullable=False)  # 返佣类型: direct(直接), indirect(间接)
    commission_rate = Column(DECIMAL(5, 4), nullable=False)  # 返佣比例
    order_amount = Column(DECIMAL(10, 4), nullable=False)  # 订单金额
    commission_amount = Column(DECIMAL(10, 4), nullable=False)  # 返佣金额
    status = Column(String(20), default="pending")  # 状态: pending, paid, cancelled
    description = Column(Text, nullable=True)  # 描述
    created_at = Column(DateTime, default=func.now())
    paid_at = Column(DateTime, nullable=True)  # 支付时间
    
    # 关系
    agent = relationship("User", foreign_keys=[agent_id], back_populates="commission_records")
    consumer = relationship("User", foreign_keys=[consumer_id])
    order = relationship("Order")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "consumer_id": self.consumer_id,
            "order_id": self.order_id,
            "commission_type": self.commission_type,
            "commission_rate": float(self.commission_rate),
            "order_amount": float(self.order_amount),
            "commission_amount": float(self.commission_amount),
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None
        }

class CommissionConfig(Base):
    """返佣配置模型"""
    __tablename__ = "commission_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_level = Column(Integer, nullable=False)  # 代理等级
    direct_rate = Column(DECIMAL(5, 4), nullable=False)  # 直接邀请返佣比例
    indirect_rate = Column(DECIMAL(5, 4), nullable=False)  # 间接邀请返佣比例
    max_levels = Column(Integer, default=3)  # 最大返佣层级
    is_active = Column(Boolean, default=True)  # 是否启用
    description = Column(Text, nullable=True)  # 描述
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "agent_level": self.agent_level,
            "direct_rate": float(self.direct_rate),
            "indirect_rate": float(self.indirect_rate),
            "max_levels": self.max_levels,
            "is_active": self.is_active,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
