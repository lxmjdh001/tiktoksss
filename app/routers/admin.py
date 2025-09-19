"""
管理员路由
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import get_current_user, User
from app.models.order import Order
from app.models.service_price import ServicePrice
from app.config import settings
from decimal import Decimal
from typing import Optional
from sqlalchemy import text

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def check_admin_permission(user: User) -> bool:
    """检查管理员权限"""
    # 这里可以根据需要设置管理员权限检查逻辑
    # 例如：特定邮箱、特定用户ID或特定会员等级
    admin_emails = ["admin@example.com", "lxmjdh@example.com", "lxmjdh1@gmail.com"]
    return user.email in admin_emails or user.member_level >= 4

@router.get("/lxmjdh", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """管理员控制台"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    # 检查管理员权限
    if not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取统计数据
    total_users = db.query(User).count()
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    completed_orders = db.query(Order).filter(Order.status == "completed").count()
    
    # 获取所有用户
    users = db.query(User).order_by(User.created_at.desc()).limit(50).all()
    
    return templates.TemplateResponse("admin/lxmjdh.html", {
        "request": request,
        "title": "管理员控制台",
        "user": user,
        "total_users": total_users,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "users": users
    })

@router.post("/lxmjdh/update-price")
async def update_service_price(
    request: Request,
    service_id: int = Form(...),
    service_name: str = Form(None),  # 改为可选
    new_price: float = Form(...),
    db: Session = Depends(get_db)
):
    """更新服务客户价格"""
    # 检查管理员权限
    user = await get_current_user(request)
    if not user or not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找或创建服务价格记录
    service_price = db.query(ServicePrice).filter(ServicePrice.service_id == service_id).first()
    
    if service_price:
        # 更新现有记录
        if service_name and service_name.strip():  # 只有当服务名称不为空时才更新
            service_price.service_name = service_name.strip()
            name_update_msg = f"名称已更新为 '{service_name.strip()}'，"
        else:
            name_update_msg = ""
        
        service_price.customer_price = Decimal(str(new_price))
        db.commit()
        
        # 计算利润（按1:7.3汇率换算）
        EXCHANGE_RATE = 7.3
        api_price_rmb = float(service_price.api_price) * EXCHANGE_RATE
        profit = float(service_price.customer_price) - api_price_rmb
        profit_rate = (profit / api_price_rmb) * 100 if api_price_rmb > 0 else 0
        
        return {
            "success": True, 
            "message": f"服务 {service_id} {name_update_msg}客户价格已更新为 ¥{new_price}",
            "profit": f"¥{profit:.4f}",
            "profit_rate": f"{profit_rate:.2f}%"
        }
    else:
        # 创建新记录（需要从API获取基本信息）
        try:
            from app.services.appfuwu_client import appfuwu_client
            services = await appfuwu_client.get_services()
            api_service = None
            
            print(f"正在查找服务ID: {service_id}")
            print(f"API返回的服务数量: {len(services)}")
            
            for service in services:
                service_id_from_api = service.get("service")
                print(f"检查服务: {service.get('name')} (ID: {service_id_from_api})")
                if service_id_from_api == service_id:
                    api_service = service
                    print(f"找到匹配的服务: {api_service}")
                    break
            
            if not api_service:
                return {"success": False, "message": f"服务 {service_id} 不存在于API中。请检查服务ID是否正确。"}
            
            # 创建新的服务价格记录
            # 如果用户没有提供服务名称，使用API返回的名称
            final_service_name = service_name.strip() if service_name and service_name.strip() else api_service.get("name", f"服务{service_id}")
            
            new_service_price = ServicePrice(
                service_id=service_id,
                service_name=final_service_name,
                api_price=Decimal(str(api_service.get("rate", 0))),
                customer_price=Decimal(str(new_price)),
                min_quantity=int(api_service.get("min", 1)),
                max_quantity=int(api_service.get("max", 10000))
            )
            
            db.add(new_service_price)
            db.commit()
            
            # 计算利润（按1:7.3汇率换算）
            EXCHANGE_RATE = 7.3
            api_price_rmb = float(new_service_price.api_price) * EXCHANGE_RATE
            profit = float(new_service_price.customer_price) - api_price_rmb
            profit_rate = (profit / api_price_rmb) * 100 if api_price_rmb > 0 else 0
            
            return {
                "success": True, 
                "message": f"服务 {service_id} 名称已设置为 '{final_service_name}'，客户价格已设置为 ¥{new_price}",
                "profit": f"¥{profit:.4f}",
                "profit_rate": f"{profit_rate:.2f}%"
            }
            
        except Exception as e:
            print(f"创建服务价格记录时出错: {str(e)}")
            return {"success": False, "message": f"更新失败: {str(e)}"}

@router.post("/lxmjdh/recharge-balance")
async def recharge_user_balance(
    request: Request,
    user_id: int = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    """为用户充值余额"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找目标用户
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户余额
    target_user.balance = Decimal(str(target_user.balance)) + Decimal(str(amount))
    db.commit()
    
    return {"success": True, "message": f"用户 {target_user.username} 余额已增加 ¥{amount}"}

@router.get("/lxmjdh/users", response_class=HTMLResponse)
async def manage_users(request: Request, db: Session = Depends(get_db)):
    """用户管理页面"""
    # 检查管理员权限
    user = await get_current_user(request)
    if not user or not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取所有用户
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "title": "用户管理",
        "user": user,
        "users": users
    })

@router.post("/lxmjdh/users/{user_id}/update-level")
async def update_user_level(
    request: Request,
    user_id: int,
    member_level: int = Form(...),
    db: Session = Depends(get_db)
):
    """更新用户会员等级"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找目标用户
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新会员等级
    target_user.member_level = member_level
    db.commit()
    
    return {"success": True, "message": f"用户 {target_user.username} 会员等级已更新为 {member_level}"}

@router.post("/lxmjdh/users/{user_id}/update")
async def update_user_info(
    request: Request,
    user_id: int,
    member_level: int = Form(...),
    total_consumed: float = Form(...),
    total_cashback: float = Form(...),
    custom_commission: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找目标用户
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户信息
    target_user.member_level = member_level
    target_user.total_consumed = Decimal(str(total_consumed))
    target_user.total_cashback = Decimal(str(total_cashback))
    
    # 如果有自定义返佣比例，可以存储到用户的自定义字段中
    # 这里暂时存储到api_key字段作为示例，实际项目中可以添加新字段
    if custom_commission is not None:
        target_user.api_key = f"custom_commission:{custom_commission}"
    
    db.commit()
    
    return {"success": True, "message": f"用户 {target_user.username} 信息已更新"}

@router.post("/lxmjdh/users/{user_id}/delete")
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """删除用户"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找目标用户
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 防止删除管理员用户
    if target_user.email in ["lxmjdh@example.com", "admin@example.com"]:
        raise HTTPException(status_code=400, detail="不能删除管理员用户")
    
    # 软删除：将状态设置为禁用
    target_user.status = 0
    db.commit()
    
    return {"success": True, "message": f"用户 {target_user.username} 已删除"}

@router.get("/lxmjdh/api-settings", response_class=HTMLResponse)
async def api_settings_page(request: Request, db: Session = Depends(get_db)):
    """API设置页面"""
    # 检查管理员权限
    user = await get_current_user(request)
    if not user or not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取当前API设置
    current_platform = "appfuwu"  # 默认使用APPFUWU
    current_api_key = None
    
    try:
        # 获取当前API密钥
        result = db.execute(text("SELECT setting_value FROM settings WHERE setting_key = 'appfuwu_api_key'"))
        row = result.fetchone()
        if row:
            current_api_key = row[0]
    except:
        pass
    
    return templates.TemplateResponse("admin/api_settings.html", {
        "request": request,
        "title": "API设置",
        "user": user,
        "current_platform": current_platform,
        "current_api_key": current_api_key
    })

@router.post("/lxmjdh/api-settings/update")
async def update_api_settings(
    request: Request,
    api_platform: str = Form(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """更新API设置"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        # 根据平台选择更新相应的API密钥
        if api_platform == "appfuwu":
            # 更新APPFUWU API密钥
            db.execute(text("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value, description, updated_at) 
                VALUES ('appfuwu_api_key', :api_key, 'APPFUWU API密钥', datetime('now'))
            """), {"api_key": api_key})
            
            # 更新API URL
            db.execute(text("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value, description, updated_at) 
                VALUES ('appfuwu_api_url', 'https://appfuwu.icu/api/v2', 'APPFUWU API地址', datetime('now'))
            """))
            
        elif api_platform == "shangfen":
            # 更新Shangfen API密钥
            db.execute(text("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value, description, updated_at) 
                VALUES ('shangfen_api_key', :api_key, 'Shangfen API密钥', datetime('now'))
            """), {"api_key": api_key})
            
            # 更新API URL
            db.execute(text("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value, description, updated_at) 
                VALUES ('shangfen_api_url', 'https://shangfen622.info/api/v2', 'Shangfen API地址', datetime('now'))
            """))
        
        # 更新当前使用的平台
        db.execute(text("""
            INSERT OR REPLACE INTO settings (setting_key, setting_value, description, updated_at) 
            VALUES ('current_api_platform', :platform, '当前使用的API平台', datetime('now'))
        """), {"platform": api_platform})
        
        db.commit()
        
        return {"success": True, "message": f"API设置已更新为 {api_platform} 平台"}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"更新失败: {str(e)}"}

@router.post("/lxmjdh/api-settings/test")
async def test_api_connection(
    request: Request,
    api_platform: str = Form(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """测试API连接"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        if api_platform == "appfuwu":
            from app.services.appfuwu_client import appfuwu_client
            # 临时设置API密钥进行测试
            await appfuwu_client.set_api_key(api_key)
            
            # 测试获取服务列表
            services = await appfuwu_client.get_services()
            if services:
                return {"success": True, "message": f"APPFUWU API连接成功！获取到 {len(services)} 个服务"}
            else:
                return {"success": False, "message": "APPFUWU API连接失败：未获取到服务列表"}
                
        elif api_platform == "shangfen":
            # 这里可以添加Shangfen API的测试逻辑
            return {"success": False, "message": "Shangfen API测试功能暂未实现"}
        
        return {"success": False, "message": "不支持的API平台"}
        
    except Exception as e:
        return {"success": False, "message": f"API连接测试失败: {str(e)}"}

@router.get("/lxmjdh/profit-analysis", response_class=HTMLResponse)
async def profit_analysis_page(request: Request, db: Session = Depends(get_db)):
    """利润分析页面"""
    # 检查管理员权限
    user = await get_current_user(request)
    if not user or not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取所有服务价格信息
    service_prices = db.query(ServicePrice).filter(ServicePrice.is_active == True).all()
    
    # 汇率设置：1美元 = 7.3人民币
    EXCHANGE_RATE = 7.3
    
    # 计算利润数据
    profit_data = []
    total_profit = 0
    total_api_cost_rmb = 0  # API成本价换算成人民币
    total_customer_revenue = 0
    
    for sp in service_prices:
        api_price_usd = float(sp.api_price)  # API价格（美元）
        api_price_rmb = api_price_usd * EXCHANGE_RATE  # 换算成人民币
        customer_price = float(sp.customer_price)  # 客户价格（人民币）
        profit = customer_price - api_price_rmb  # 利润 = 客户价格 - 换算后的成本价
        profit_rate = (profit / api_price_rmb) * 100 if api_price_rmb > 0 else 0
        
        profit_data.append({
            "service_id": sp.service_id,
            "service_name": sp.service_name,
            "api_price_usd": api_price_usd,  # 原始API价格（美元）
            "api_price_rmb": api_price_rmb,  # 换算后的API价格（人民币）
            "customer_price": customer_price,
            "profit": profit,
            "profit_rate": profit_rate,
            "min_quantity": sp.min_quantity,
            "max_quantity": sp.max_quantity
        })
        
        total_api_cost_rmb += api_price_rmb
        total_customer_revenue += customer_price
        total_profit += profit
    
    # 计算总体利润率
    overall_profit_rate = (total_profit / total_api_cost_rmb) * 100 if total_api_cost_rmb > 0 else 0
    
    return templates.TemplateResponse("admin/profit_analysis.html", {
        "request": request,
        "title": "利润分析",
        "user": user,
        "profit_data": profit_data,
        "total_profit": total_profit,
        "total_api_cost": total_api_cost_rmb,  # 使用换算后的成本价
        "total_customer_revenue": total_customer_revenue,
        "overall_profit_rate": overall_profit_rate
    })
