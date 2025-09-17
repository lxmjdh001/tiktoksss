"""
认证路由
"""
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import authenticate_user, create_user, get_current_user
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="/Users/chaoteng/Desktop/7c/tiktok/python_backend/app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    # 如果已登录，重定向到控制台
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "title": "用户登录"
    })

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """处理登录"""
    user = await authenticate_user(email, password)
    if not user:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "title": "用户登录",
            "error": "邮箱或密码错误"
        })
    
    # 设置会话
    request.session["user_id"] = user.id
    request.session["email"] = user.email
    request.session["username"] = user.username
    request.session["member_level"] = user.member_level
    request.session["balance"] = float(user.balance)
    
    return RedirectResponse(url="/admin/dashboard", status_code=302)

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页面"""
    # 如果已登录，重定向到控制台
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    return templates.TemplateResponse("auth/register.html", {
        "request": request,
        "title": "用户注册"
    })

@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    invite_code: str = Form(None)
):
    """处理注册"""
    if password != confirm_password:
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "title": "用户注册",
            "error": "两次输入的密码不一致"
        })
    
    user = await create_user(email, username, password, invite_code)
    if not user:
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "title": "用户注册",
            "error": "邮箱已被注册"
        })
    
    # 设置会话
    request.session["user_id"] = user.id
    request.session["email"] = user.email
    request.session["username"] = user.username
    request.session["member_level"] = user.member_level
    request.session["balance"] = float(user.balance)
    
    return RedirectResponse(url="/admin/dashboard", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    """退出登录"""
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=302)
