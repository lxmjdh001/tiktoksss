"""
TikTok API 管理后台 - FastAPI版本
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import os

from app.routers import auth, dashboard, orders, admin, recharge, agent, agent_dashboard
from app.database import init_db
from app.models.user import get_current_user

# 导入所有模型以确保它们被注册
from app.models import user, order, member_level, commission

# 创建FastAPI应用
app = FastAPI(
    title="TikTok API 管理后台",
    description="基于FastAPI的TikTok API管理系统",
    version="1.0.0"
)

# 添加SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here-change-in-production")

# 静态文件和模板
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="/Users/chaoteng/Desktop/7c/tiktok/python_backend/app/templates")

# 安全
security = HTTPBearer()

# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["认证"])
app.include_router(dashboard.router, prefix="/admin", tags=["控制台"])
app.include_router(orders.router, prefix="/api", tags=["API接口"])
app.include_router(admin.router, prefix="/admin", tags=["管理员"])
app.include_router(recharge.router, tags=["充值"])
app.include_router(agent.router, tags=["代理管理"])
app.include_router(agent_dashboard.router, tags=["代理界面"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """首页 - 重定向到登录或控制台"""
    try:
        user = await get_current_user(request)
        if user:
            return RedirectResponse(url="/admin/dashboard", status_code=302)
    except:
        pass
    return RedirectResponse(url="/auth/login", status_code=302)

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "TikTok API 管理后台运行正常"}

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    await init_db()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    )
