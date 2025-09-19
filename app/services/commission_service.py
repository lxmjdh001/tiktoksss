"""
返佣计算服务
"""
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.commission import CommissionRecord
from app.models.order import Order
from decimal import Decimal
from typing import List, Dict

class CommissionService:
    """返佣计算服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_commission(self, order: Order) -> List[CommissionRecord]:
        """计算订单返佣"""
        consumer = self.db.query(User).filter(User.id == order.user_id).first()
        if not consumer:
            return []
        
        commission_records = []
        
        # 获取邀请链
        invite_chain = self._get_invite_chain(consumer)
        
        # 为每个层级的代理计算返佣
        for level, agent in enumerate(invite_chain):
            if not agent.is_agent:
                continue
            
            # 确定返佣类型和比例
            if level == 0:
                commission_type = "direct"
                commission_rate = Decimal("0.05")  # 直接邀请返佣 5%
            else:
                commission_type = "indirect"
                commission_rate = Decimal("0.02")  # 间接邀请返佣 2%
            
            # 计算返佣金额
            commission_amount = Decimal(str(order.charge)) * commission_rate
            
            # 创建返佣记录
            commission_record = CommissionRecord(
                agent_id=agent.id,
                consumer_id=consumer.id,
                order_id=order.id,
                commission_type=commission_type,
                commission_rate=commission_rate,
                order_amount=order.charge,
                commission_amount=commission_amount,
                status="pending",
                description=f"订单 {order.id} 的{commission_type}返佣"
            )
            
            self.db.add(commission_record)
            commission_records.append(commission_record)
            
            # 更新代理的返佣统计
            if commission_type == "direct":
                agent.total_direct_commission += commission_amount
            else:
                agent.total_indirect_commission += commission_amount
            
            agent.total_commission += commission_amount
            
            # 将返佣金额添加到代理余额
            agent.balance += commission_amount
        
        self.db.commit()
        return commission_records
    
    def _get_invite_chain(self, user: User, max_levels: int = 3) -> List[User]:
        """获取邀请链"""
        chain = []
        current_user = user
        level = 0
        
        while current_user.inviter_id and level < max_levels:
            inviter = self.db.query(User).filter(User.id == current_user.inviter_id).first()
            if not inviter:
                break
            
            chain.append(inviter)
            current_user = inviter
            level += 1
        
        return chain
    
    def get_agent_stats(self, agent_id: int) -> Dict:
        """获取代理统计信息"""
        agent = self.db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not agent:
            return {}
        
        # 获取直接邀请的用户数量
        direct_invitees = self.db.query(User).filter(User.inviter_id == agent_id).count()
        
        # 获取间接邀请的用户数量（通过邀请链）
        indirect_invitees = 0
        direct_users = self.db.query(User).filter(User.inviter_id == agent_id).all()
        for user in direct_users:
            indirect_count = self.db.query(User).filter(User.inviter_id == user.id).count()
            indirect_invitees += indirect_count
        
        # 获取返佣记录统计
        total_commission_records = self.db.query(CommissionRecord).filter(
            CommissionRecord.agent_id == agent_id
        ).count()
        
        pending_commission = self.db.query(CommissionRecord).filter(
            CommissionRecord.agent_id == agent_id,
            CommissionRecord.status == "pending"
        ).count()
        
        paid_commission = self.db.query(CommissionRecord).filter(
            CommissionRecord.agent_id == agent_id,
            CommissionRecord.status == "paid"
        ).count()
        
        return {
            "agent": agent,
            "direct_invitees": direct_invitees,
            "indirect_invitees": indirect_invitees,
            "total_invitees": direct_invitees + indirect_invitees,
            "total_commission_records": total_commission_records,
            "pending_commission": pending_commission,
            "paid_commission": paid_commission,
            "total_direct_commission": float(agent.total_direct_commission),
            "total_indirect_commission": float(agent.total_indirect_commission),
            "total_commission": float(agent.total_commission)
        }
    
    def get_invite_tree(self, root_agent_id: int, max_depth: int = 3) -> Dict:
        """获取邀请树结构"""
        def build_tree(user_id: int, depth: int = 0) -> Dict:
            if depth >= max_depth:
                return None
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # 获取直接邀请的用户
            invitees = self.db.query(User).filter(User.inviter_id == user_id).all()
            
            children = []
            for invitee in invitees:
                child_tree = build_tree(invitee.id, depth + 1)
                if child_tree:
                    children.append(child_tree)
            
            return {
                "user": user,
                "depth": depth,
                "children": children,
                "children_count": len(children)
            }
        
        return build_tree(root_agent_id)
    
    def pay_commission(self, commission_record_id: int) -> bool:
        """支付返佣"""
        commission_record = self.db.query(CommissionRecord).filter(
            CommissionRecord.id == commission_record_id
        ).first()
        
        if not commission_record or commission_record.status != "pending":
            return False
        
        try:
            # 更新返佣记录状态
            commission_record.status = "paid"
            commission_record.paid_at = func.now()
            
            self.db.commit()
            return True
            
        except Exception:
            self.db.rollback()
            return False
