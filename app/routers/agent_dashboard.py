"""
代理页面路由
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models.user import get_current_user, User
from app.models.commission import CommissionRecord
from app.models.order import Order
from decimal import Decimal
from typing import Dict, Any
import qrcode
import io
import base64

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/agent", response_class=HTMLResponse)
async def agent_page(request: Request, db: Session = Depends(get_db)):
    """代理页面"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    # 获取代理统计信息
    stats = await get_agent_stats(user.id, db)
    
    # 获取最近邀请的用户
    recent_invitees = db.query(User).filter(
        User.inviter_id == user.id
    ).order_by(desc(User.created_at)).limit(10).all()
    
    return templates.TemplateResponse("agent.html", {
        "request": request,
        "title": "代理中心",
        "user": user,
        "stats": stats,
        "recent_invitees": recent_invitees
    })

@router.get("/agent/qrcode")
async def generate_qr_code(request: Request, db: Session = Depends(get_db)):
    """生成邀请二维码"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 生成邀请链接
    invite_link = f"{request.url.scheme}://{request.url.netloc}/auth/register?invite_code={user.invite_code}"
    
    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(invite_link)
    qr.make(fit=True)
    
    # 创建二维码图片
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 转换为base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "success": True,
        "qr_code": f"data:image/png;base64,{img_base64}",
        "invite_link": invite_link
    }

@router.get("/agent/stats")
async def get_agent_stats_api(request: Request, db: Session = Depends(get_db)):
    """获取代理统计信息API"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 获取统计信息
    stats = await get_agent_stats(user.id, db)
    
    return {
        "success": True,
        "stats": stats,
        "user_info": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "invite_code": user.invite_code,
            "is_agent": user.is_agent,
            "agent_level": user.agent_level,
            "direct_commission_rate": float(user.direct_commission_rate),
            "indirect_commission_rate": float(user.indirect_commission_rate)
        }
    }

@router.get("/agent/invitees")
async def get_invitees_api(request: Request, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    """获取邀请用户列表API"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 计算偏移量
    offset = (page - 1) * limit
    
    # 获取邀请用户
    invitees = db.query(User).filter(
        User.inviter_id == user.id
    ).order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    
    # 获取总数
    total_count = db.query(User).filter(User.inviter_id == user.id).count()
    
    # 计算每个用户的统计信息
    invitee_list = []
    for invitee in invitees:
        # 订单统计
        total_orders = db.query(Order).filter(Order.user_id == invitee.id).count()
        total_consumed = db.query(func.sum(Order.charge)).filter(
            Order.user_id == invitee.id
        ).scalar() or Decimal('0')
        
        # 返佣统计
        total_commission = db.query(func.sum(CommissionRecord.commission_amount)).filter(
            CommissionRecord.agent_id == user.id,
            CommissionRecord.consumer_id == invitee.id
        ).scalar() or Decimal('0')
        
        invitee_list.append({
            "id": invitee.id,
            "username": invitee.username,
            "email": invitee.email,
            "is_agent": invitee.is_agent,
            "agent_level": invitee.agent_level,
            "created_at": invitee.created_at.isoformat() if invitee.created_at else None,
            "total_orders": total_orders,
            "total_consumed": float(total_consumed),
            "total_commission": float(total_commission)
        })
    
    return {
        "success": True,
        "invitees": invitee_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

@router.get("/agent/commissions")
async def get_commissions_api(request: Request, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    """获取返佣记录API"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 计算偏移量
    offset = (page - 1) * limit
    
    # 获取返佣记录
    commissions = db.query(CommissionRecord).filter(
        CommissionRecord.agent_id == user.id
    ).order_by(desc(CommissionRecord.created_at)).offset(offset).limit(limit).all()
    
    # 获取总数
    total_count = db.query(CommissionRecord).filter(CommissionRecord.agent_id == user.id).count()
    
    # 添加详细信息
    commission_list = []
    for commission in commissions:
        consumer = db.query(User).filter(User.id == commission.consumer_id).first()
        order = db.query(Order).filter(Order.id == commission.order_id).first()
        
        commission_list.append({
            "id": commission.id,
            "commission_type": commission.commission_type,
            "commission_rate": float(commission.commission_rate),
            "order_amount": float(commission.order_amount),
            "commission_amount": float(commission.commission_amount),
            "status": commission.status,
            "created_at": commission.created_at.isoformat() if commission.created_at else None,
            "paid_at": commission.paid_at.isoformat() if commission.paid_at else None,
            "consumer": {
                "id": consumer.id if consumer else None,
                "username": consumer.username if consumer else "未知用户",
                "email": consumer.email if consumer else None
            },
            "order": {
                "id": order.id if order else None,
                "service_name": order.service_name if order else None,
                "quantity": order.quantity if order else None
            }
        })
    
    return {
        "success": True,
        "commissions": commission_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }


async def get_agent_stats(agent_id: int, db: Session) -> Dict[str, Any]:
    """获取代理统计信息"""
    # 总邀请用户数
    total_invitees = db.query(User).filter(User.inviter_id == agent_id).count()
    
    # 活跃邀请用户数（有订单的用户）
    active_invitees = db.query(User).join(Order).filter(
        User.inviter_id == agent_id
    ).distinct().count()
    
    # 总返佣金额
    total_commission = db.query(func.sum(CommissionRecord.commission_amount)).filter(
        CommissionRecord.agent_id == agent_id
    ).scalar() or Decimal('0')
    
    # 本月返佣金额
    from datetime import datetime, timedelta
    this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_commission = db.query(func.sum(CommissionRecord.commission_amount)).filter(
        CommissionRecord.agent_id == agent_id,
        CommissionRecord.created_at >= this_month_start
    ).scalar() or Decimal('0')
    
    # 总下级消费金额
    total_consumption = db.query(func.sum(Order.charge)).join(User).filter(
        User.inviter_id == agent_id
    ).scalar() or Decimal('0')
    
    return {
        'total_invitees': total_invitees,
        'active_invitees': active_invitees,
        'total_commission': total_commission,
        'monthly_commission': monthly_commission,
        'total_consumption': total_consumption
    }
