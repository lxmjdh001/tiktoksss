"""
代理管理路由
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from app.database import get_db
from app.models.user import get_current_user, User
from app.models.commission import CommissionRecord, CommissionConfig
from app.models.order import Order
from decimal import Decimal
from typing import Optional, List
import secrets
import string

router = APIRouter()
templates = Jinja2Templates(directory="/Users/chaoteng/Desktop/7c/tiktok/python_backend/app/templates")

def check_admin_permission(user: User) -> bool:
    """检查管理员权限"""
    admin_emails = ["admin@example.com", "lxmjdh@example.com", "lxmjdh1@gmail.com"]
    return user.email in admin_emails or user.member_level >= 4

def generate_invite_code() -> str:
    """生成邀请码"""
    return ''.join(secrets.choices(string.ascii_uppercase + string.digits, k=8))

@router.get("/admin/agents", response_class=HTMLResponse)
async def agents_management(request: Request, db: Session = Depends(get_db)):
    """代理管理页面"""
    # 检查管理员权限
    user = await get_current_user(request)
    if not user or not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取所有代理
    agents = db.query(User).filter(User.is_agent == True).order_by(desc(User.created_at)).all()
    
    # 获取代理统计信息
    total_agents = len(agents)
    active_agents = len([a for a in agents if a.status == 1])
    
    return templates.TemplateResponse("admin/agents.html", {
        "request": request,
        "title": "代理管理",
        "user": user,
        "agents": agents,
        "total_agents": total_agents,
        "active_agents": active_agents
    })

@router.post("/admin/agents/set-agent")
async def set_agent(
    request: Request,
    user_id: int = Form(...),
    agent_level: int = Form(...),
    direct_rate: float = Form(...),
    indirect_rate: float = Form(...),
    db: Session = Depends(get_db)
):
    """设置用户为代理"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找目标用户
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 设置代理信息
        target_user.is_agent = True
        target_user.agent_level = agent_level
        target_user.direct_commission_rate = Decimal(str(direct_rate))
        target_user.indirect_commission_rate = Decimal(str(indirect_rate))
        
        # 生成邀请码（如果还没有）
        if not target_user.invite_code:
            target_user.invite_code = generate_invite_code()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"用户 {target_user.username} 已设置为 {agent_level} 级代理",
            "invite_code": target_user.invite_code
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"设置失败: {str(e)}"}

@router.post("/admin/agents/update-commission")
async def update_agent_commission(
    request: Request,
    agent_id: int = Form(...),
    direct_rate: float = Form(...),
    indirect_rate: float = Form(...),
    db: Session = Depends(get_db)
):
    """更新代理返佣比例"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找代理
    agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
    if not agent:
        raise HTTPException(status_code=404, detail="代理不存在")
    
    try:
        # 更新返佣比例
        agent.direct_commission_rate = Decimal(str(direct_rate))
        agent.indirect_commission_rate = Decimal(str(indirect_rate))
        
        db.commit()
        
        return {
            "success": True,
            "message": f"代理 {agent.username} 的返佣比例已更新"
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"更新失败: {str(e)}"}

@router.get("/admin/agents/commission-records", response_class=HTMLResponse)
async def commission_records(request: Request, agent_id: Optional[int] = None, db: Session = Depends(get_db)):
    """返佣记录页面"""
    # 检查管理员权限
    user = await get_current_user(request)
    if not user or not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取返佣记录
    query = db.query(CommissionRecord).join(User, CommissionRecord.agent_id == User.id)
    
    if agent_id:
        query = query.filter(CommissionRecord.agent_id == agent_id)
    
    records = query.order_by(desc(CommissionRecord.created_at)).limit(100).all()
    
    # 获取代理列表
    agents = db.query(User).filter(User.is_agent == True).all()
    
    return templates.TemplateResponse("admin/commission_records.html", {
        "request": request,
        "title": "返佣记录",
        "user": user,
        "records": records,
        "agents": agents,
        "selected_agent_id": agent_id
    })

@router.get("/admin/agents/commission-config", response_class=HTMLResponse)
async def commission_config(request: Request, db: Session = Depends(get_db)):
    """返佣配置页面"""
    # 检查管理员权限
    user = await get_current_user(request)
    if not user or not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取返佣配置
    configs = db.query(CommissionConfig).order_by(CommissionConfig.agent_level).all()
    
    return templates.TemplateResponse("admin/commission_config.html", {
        "request": request,
        "title": "返佣配置",
        "user": user,
        "configs": configs
    })

@router.post("/admin/agents/commission-config/update")
async def update_commission_config(
    request: Request,
    config_id: int = Form(...),
    direct_rate: float = Form(...),
    indirect_rate: float = Form(...),
    max_levels: int = Form(...),
    db: Session = Depends(get_db)
):
    """更新返佣配置"""
    # 检查管理员权限
    admin_user = await get_current_user(request)
    if not admin_user or not check_admin_permission(admin_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找配置
    config = db.query(CommissionConfig).filter(CommissionConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    try:
        # 更新配置
        config.direct_rate = Decimal(str(direct_rate))
        config.indirect_rate = Decimal(str(indirect_rate))
        config.max_levels = max_levels
        
        db.commit()
        
        return {
            "success": True,
            "message": f"代理等级 {config.agent_level} 的返佣配置已更新"
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"更新失败: {str(e)}"}

@router.get("/admin/agents/invite-tree", response_class=HTMLResponse)
async def invite_tree(request: Request, agent_id: Optional[int] = None, db: Session = Depends(get_db)):
    """邀请树页面"""
    # 检查管理员权限
    user = await get_current_user(request)
    if not user or not check_admin_permission(user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取邀请树数据
    if agent_id:
        # 获取特定代理的邀请树
        root_agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not root_agent:
            raise HTTPException(status_code=404, detail="代理不存在")
        
        # 递归获取邀请树
        def get_invite_tree(user_id: int, level: int = 0) -> dict:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            invitees = db.query(User).filter(User.inviter_id == user_id).all()
            children = []
            
            for invitee in invitees:
                child_tree = get_invite_tree(invitee.id, level + 1)
                if child_tree:
                    children.append(child_tree)
            
            return {
                "user": user,
                "level": level,
                "children": children
            }
        
        tree_data = get_invite_tree(agent_id)
    else:
        tree_data = None
    
    # 获取所有代理
    agents = db.query(User).filter(User.is_agent == True).all()
    
    return templates.TemplateResponse("admin/invite_tree.html", {
        "request": request,
        "title": "邀请树",
        "user": user,
        "tree_data": tree_data,
        "agents": agents,
        "selected_agent_id": agent_id
    })
