#!/usr/bin/env python3
"""
测试 APPFUWU API 集成
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.appfuwu_client import appfuwu_client

async def test_api():
    """测试API功能"""
    print("🧪 开始测试 APPFUWU API 集成...")
    print("=" * 50)
    
    try:
        # 测试获取服务列表
        print("1. 测试获取服务列表...")
        services = await appfuwu_client.get_services()
        print(f"   获取到 {len(services)} 个服务")
        
        if services:
            print("   前3个服务示例:")
            for i, service in enumerate(services[:3]):
                print(f"   - ID: {service.get('service')}, 名称: {service.get('name')}, 价格: {service.get('rate')}")
        
        # 测试获取抖音服务
        print("\n2. 测试获取抖音服务...")
        douyin_services = await appfuwu_client.get_douyin_services()
        print(f"   获取到 {len(douyin_services)} 个抖音相关服务")
        
        if douyin_services:
            print("   抖音服务示例:")
            for service in douyin_services[:3]:
                print(f"   - ID: {service.get('id')}, 名称: {service.get('name')}, 价格: {service.get('price')}")
        
        # 测试获取余额（需要API密钥）
        print("\n3. 测试获取账户余额...")
        try:
            balance = await appfuwu_client.get_balance()
            print(f"   账户余额: ${balance}")
        except Exception as e:
            print(f"   获取余额失败: {e}")
            print("   (这需要先设置API密钥)")
        
        print("\n✅ API集成测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭客户端
        await appfuwu_client.close()

if __name__ == "__main__":
    asyncio.run(test_api())
