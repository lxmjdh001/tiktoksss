"""
数据库配置和初始化
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

from app.config import settings

# 确保数据库目录存在
os.makedirs("database", exist_ok=True)

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite特定设置
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """初始化数据库表"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 插入默认数据
    db = SessionLocal()
    try:
        # 检查是否已有数据
        result = db.execute(text("SELECT COUNT(*) FROM member_levels"))
        count = result.scalar()
        
        if count == 0:
            # 插入默认会员等级
            db.execute(text("""
                INSERT INTO member_levels (id, name, min_consumption, cashback_rate, max_orders, status, created_at) 
                VALUES 
                (1, '普通会员', 0.00, 0.0200, 100, 1, datetime('now')),
                (2, 'VIP会员', 100.00, 0.1000, 1000, 1, datetime('now')),
                (3, '钻石会员', 500.00, 0.1500, 5000, 1, datetime('now')),
                (4, '至尊会员', 2000.00, 0.2000, 10000, 1, datetime('now'))
            """))
            
            # 插入默认设置
            db.execute(text("""
                INSERT INTO settings (setting_key, setting_value, description, updated_at) 
                VALUES 
                ('shangfen_api_url', 'https://shangfen622.info/api/v2', 'Shangfen API地址', datetime('now')),
                ('site_name', 'TikTok API管理后台', '网站名称', datetime('now')),
                ('default_member_level', '1', '默认会员等级', datetime('now'))
            """))
            
            db.commit()
            print("✅ Shangfen API数据库初始化完成")
        else:
            print("✅ Shangfen API数据库已存在，跳过初始化")
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        db.rollback()
    finally:
        db.close()
