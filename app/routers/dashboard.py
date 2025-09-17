"""
控制台路由
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import get_current_user, User
from app.models.order import Order
from app.models.service_price import ServicePrice
from app.config import settings
from app.services.appfuwu_client import appfuwu_client

router = APIRouter()
templates = Jinja2Templates(directory="/Users/chaoteng/Desktop/7c/tiktok/python_backend/app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """控制台首页"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    # 获取用户统计信息
    total_orders = db.query(Order).filter(Order.user_id == user.id).count()
    pending_orders = db.query(Order).filter(
        Order.user_id == user.id, 
        Order.status == "pending"
    ).count()
    completed_orders = db.query(Order).filter(
        Order.user_id == user.id, 
        Order.status == "completed"
    ).count()
    
    # 获取最近订单（最多3条）
    recent_orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(3).all()
    
    # 获取会员等级信息
    member_level_info = settings.member_levels.get(user.member_level, {
        "name": "普通会员",
        "cashback_rate": 0.02
    })
    
    # 从APPFUWU API获取服务数据
    try:
        # 获取所有平台的服务
        platform_services = await appfuwu_client.get_services_by_platform()
        
        # 获取客户价格映射
        service_prices = db.query(ServicePrice).filter(ServicePrice.is_active == True).all()
        price_map = {sp.service_id: sp for sp in service_prices}
        
        # 更新所有平台的服务价格为客户价格
        for platform, services_list in platform_services.items():
            for service in services_list:
                service_id = service.get("id")
                if service_id in price_map:
                    # 使用客户价格和自定义服务名称
                    service["price"] = float(price_map[service_id].customer_price)
                    service["api_price"] = float(price_map[service_id].api_price)  # 保留API价格用于参考
                    service["name"] = price_map[service_id].service_name  # 使用数据库中的自定义名称
                else:
                    # 如果没有设置客户价格，使用API价格
                    service["api_price"] = service.get("price", 0)
        
        services = platform_services
        
    except Exception as e:
        print(f"获取服务失败: {e}")
        services = {
            "douyin": [],
            "xiaoshou": [],
            "hudie": [],
            "toutiao": [],
            "weibo": [],
            "wechat": [],
            "bilibili": [],
            "xiaohongshu": [],
            "meituan": []
        }
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "title": "控制台",
        "user": user,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "recent_orders": recent_orders,
        "member_level_info": member_level_info,
        "services": services
    })
