"""
订单管理路由
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import get_current_user, User
from app.models.order import Order
from app.models.service_price import ServicePrice
from app.services.appfuwu_client import appfuwu_client
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

router = APIRouter()

class OrderRequest(BaseModel):
    service_id: int
    link: str
    quantity: int
    order_type: str = "fixed"
    comments: Optional[str] = None

class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    message: str

@router.post("/api/orders/submit", response_model=OrderResponse)
async def submit_order(
    order_data: OrderRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """提交订单"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    # 获取服务价格信息
    service_price = db.query(ServicePrice).filter(
        ServicePrice.service_id == order_data.service_id,
        ServicePrice.is_active == True
    ).first()
    
    if not service_price:
        raise HTTPException(status_code=400, detail="服务价格未设置")
    
    # 计算订单总价（客户价格）
    customer_total_price = Decimal(str(service_price.customer_price)) * order_data.quantity
    
    # 检查用户余额是否足够
    if user.balance < customer_total_price:
        raise HTTPException(
            status_code=400, 
            detail=f"余额不足，需要 ¥{customer_total_price}，当前余额 ¥{user.balance}"
        )
    
    try:
        # 使用API成本价提交订单到APPFUWU API
        api_result = await appfuwu_client.submit_order(
            service_id=order_data.service_id,
            link=order_data.link,
            quantity=order_data.quantity,
            order_type=order_data.order_type,
            comments=order_data.comments
        )
        
        if not api_result.get("success", False):
            raise HTTPException(status_code=400, detail=f"API订单提交失败: {api_result.get('message', '未知错误')}")
        
        # 扣除用户余额（客户价格）
        user.balance = user.balance - customer_total_price
        user.total_consumed = user.total_consumed + customer_total_price
        
        # 计算用户返现（基于会员等级）
        from app.config import settings
        member_level_info = settings.member_levels.get(user.member_level, {
            "name": "普通会员",
            "cashback_rate": 0.02
        })
        cashback_rate = Decimal(str(member_level_info["cashback_rate"]))
        cashback_amount = customer_total_price * cashback_rate
        user.total_cashback = user.total_cashback + cashback_amount
        user.balance = user.balance + cashback_amount  # 返现直接加到余额
        
        # 在本地数据库创建订单记录
        order = Order(
            user_id=user.id,
            service_id=order_data.service_id,
            service_name=service_price.service_name,
            link=order_data.link,
            quantity=order_data.quantity,
            comments=order_data.comments,  # 保存评论内容
            status="pending",
            charge=customer_total_price,  # 记录客户支付的价格
            external_order_id=api_result.get("order_id")
        )
        
        db.add(order)
        db.flush()  # 获取订单ID
        
        # 创建返现记录
        from app.models.order import CashbackRecord
        cashback_record = CashbackRecord(
            user_id=user.id,
            order_id=order.id,
            amount=cashback_amount,
            rate=cashback_rate
        )
        db.add(cashback_record)
        db.commit()
        
        # 计算代理返佣
        try:
            from app.services.commission_service import CommissionService
            commission_service = CommissionService(db)
            await commission_service.calculate_commission(order)
        except Exception as e:
            print(f"返佣计算失败: {e}")
            # 返佣计算失败不影响订单创建
        
        return OrderResponse(
            success=True,
            order_id=str(order.id),  # 返回本地订单ID
            message=f"订单提交成功！已扣除 ¥{customer_total_price}，返现 ¥{cashback_amount:.2f}，API订单ID: {api_result.get('order_id')}"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"订单提交失败: {str(e)}")

@router.get("/api/orders/{order_id}/status")
async def get_order_status(
    order_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """查询订单状态"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    result = await appfuwu_client.get_order_status(order_id)
    return result

@router.get("/api/services/douyin")
async def get_douyin_services(request: Request):
    """获取抖音服务列表"""
    services = await appfuwu_client.get_douyin_services()
    return {"success": True, "data": services}

@router.get("/api/balance")
async def get_balance(request: Request, db: Session = Depends(get_db)):
    """获取账户余额"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="用户未登录")
    
    balance = await appfuwu_client.get_balance()
    return {"success": True, "balance": balance}
