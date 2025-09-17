"""
用户相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from typing import Optional

from app.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    member_level = Column(Integer, default=1)
    balance = Column(DECIMAL(10, 2), default=0.00)
    total_consumed = Column(DECIMAL(10, 2), default=0.00)
    total_cashback = Column(DECIMAL(10, 2), default=0.00)
    api_key = Column(String(255), nullable=True)
    status = Column(Integer, default=1)
    
    # 代理邀请相关字段
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 邀请人ID
    invite_code = Column(String(20), unique=True, nullable=True)  # 邀请码
    is_agent = Column(Boolean, default=False)  # 是否为代理
    agent_level = Column(Integer, default=0)  # 代理等级 (0=普通用户, 1=一级代理, 2=二级代理...)
    direct_commission_rate = Column(DECIMAL(5, 4), default=0.0000)  # 直接邀请返佣比例
    indirect_commission_rate = Column(DECIMAL(5, 4), default=0.0000)  # 间接邀请返佣比例
    total_direct_commission = Column(DECIMAL(10, 2), default=0.00)  # 直接邀请总返佣
    total_indirect_commission = Column(DECIMAL(10, 2), default=0.00)  # 间接邀请总返佣
    total_commission = Column(DECIMAL(10, 2), default=0.00)  # 总返佣
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    orders = relationship("Order", back_populates="user", lazy="dynamic")
    cashback_records = relationship("CashbackRecord", back_populates="user", lazy="dynamic")
    recharge_records = relationship("RechargeRecord", back_populates="user", lazy="dynamic")
    
    # 邀请关系
    inviter = relationship("User", remote_side=[id], backref="invitees")  # 邀请人
    commission_records = relationship("CommissionRecord", back_populates="agent", lazy="dynamic", foreign_keys="CommissionRecord.agent_id")  # 返佣记录
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(password, self.password_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码"""
        return pwd_context.hash(password)
    
    @property
    def member_level_name(self) -> str:
        """获取会员等级名称"""
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            from app.models.member_level import MemberLevel
            level = db.query(MemberLevel).filter(MemberLevel.id == self.member_level).first()
            return level.name if level else "普通会员"
        finally:
            db.close()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "member_level": self.member_level,
            "member_level_name": self.member_level_name,
            "balance": float(self.balance),
            "total_consumed": float(self.total_consumed),
            "total_cashback": float(self.total_cashback),
            "api_key": self.api_key,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Setting(Base):
    """系统设置模型"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# 认证相关函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(request: Request) -> Optional[User]:
    """获取当前用户"""
    from app.database import SessionLocal
    
    # 从会话中获取用户ID
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.status == 1).first()
        return user
    finally:
        db.close()

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """验证用户"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email, User.status == 1).first()
        if user and user.verify_password(password):
            return user
        return None
    finally:
        db.close()

async def create_user(email: str, username: str, password: str, invite_code: str = None) -> Optional[User]:
    """创建用户"""
    from app.database import SessionLocal
    import secrets
    import string
    
    db = SessionLocal()
    try:
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return None
        
        # 查找邀请人
        inviter_id = None
        if invite_code:
            inviter = db.query(User).filter(User.invite_code == invite_code).first()
            if inviter:
                inviter_id = inviter.id
        
        # 生成邀请码
        def generate_invite_code():
            return ''.join(secrets.choices(string.ascii_uppercase + string.digits, k=8))
        
        # 创建新用户
        user = User(
            email=email,
            username=username,
            password_hash=User.hash_password(password),
            member_level=1,
            inviter_id=inviter_id,
            invite_code=generate_invite_code()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        return None
    finally:
        db.close()
