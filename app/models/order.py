"""
订单相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Order(Base):
    """订单模型"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, nullable=False)
    service_name = Column(String(255), nullable=False)
    link = Column(Text, nullable=False)
    quantity = Column(Integer, default=0)
    runs = Column(Integer, default=0)
    interval_minutes = Column(Integer, default=0)
    comments = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    charge = Column(DECIMAL(10, 4), default=0.0000)
    start_count = Column(Integer, default=0)
    remains = Column(Integer, default=0)
    currency = Column(String(10), default="USD")
    external_order_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="orders")
    cashback_records = relationship("CashbackRecord", back_populates="order")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "link": self.link,
            "quantity": self.quantity,
            "runs": self.runs,
            "interval_minutes": self.interval_minutes,
            "comments": self.comments,
            "status": self.status,
            "charge": float(self.charge),
            "start_count": self.start_count,
            "remains": self.remains,
            "currency": self.currency,
            "external_order_id": self.external_order_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class CashbackRecord(Base):
    """返现记录模型"""
    __tablename__ = "cashback_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(DECIMAL(10, 4), nullable=False)
    rate = Column(DECIMAL(5, 4), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    user = relationship("User", back_populates="cashback_records")
    order = relationship("Order", back_populates="cashback_records")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "amount": float(self.amount),
            "rate": float(self.rate),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
