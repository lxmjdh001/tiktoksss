"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """应用设置"""
    
    # 应用基本设置
    app_name: str = "TikTok API 管理后台"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 数据库设置
    database_url: str = "sqlite:///./database/shangfen_api.db"
    
    # 安全设置
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API设置
    shangfen_api_url: str = "https://shangfen622.info/api/v2"
    
    # 会员等级设置
    member_levels: dict = {
        1: {"name": "普通会员", "discount": 0, "max_orders": 100, "cashback_rate": 0.02},
        2: {"name": "VIP会员", "discount": 0.05, "max_orders": 500, "cashback_rate": 0.10},
        3: {"name": "钻石会员", "discount": 0.10, "max_orders": 1000, "cashback_rate": 0.15},
        4: {"name": "至尊会员", "discount": 0.15, "max_orders": 5000, "cashback_rate": 0.20}
    }
    
    # 分页设置
    items_per_page: int = 20
    
    class Config:
        env_file = ".env"

# 全局设置实例
settings = Settings()
