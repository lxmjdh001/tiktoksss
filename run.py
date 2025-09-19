#!/usr/bin/env python3
"""
TikTok API 管理后台启动脚本
"""
import uvicorn
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 启动TikTok API管理后台...")
    print("📱 访问地址: http://localhost:8008")
    print("🏥 健康检查: http://localhost:8008/health")
    print("🛑 按 Ctrl+C 停止服务")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    )
