#!/usr/bin/env python3
"""
测试API设置功能
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.appfuwu_client import appfuwu_client

async def test_api_settings():
    """测试API设置功能"""
    print("🧪 测试API设置功能...")
    print("=" * 50)
    
    try:
        # 测试获取API密钥
        print("1. 测试获取API密钥...")
        api_key = await appfuwu_client.get_api_key()
        if api_key:
            print(f"   ✅ API密钥已配置: {api_key[:8]}...{api_key[-8:]}")
        else:
            print("   ❌ API密钥未配置")
            return
        
        # 测试API连接
        print("\n2. 测试API连接...")
        try:
            services = await appfuwu_client.get_services()
            print(f"   ✅ API连接成功！获取到 {len(services)} 个服务")
            
            if services:
                print("   前3个服务示例:")
                for i, service in enumerate(services[:3]):
                    print(f"   - ID: {service.get('service')}, 名称: {service.get('name')}, 价格: {service.get('rate')}")
        except Exception as e:
            print(f"   ❌ API连接失败: {e}")
        
        # 测试获取抖音服务
        print("\n3. 测试获取抖音服务...")
        try:
            douyin_services = await appfuwu_client.get_douyin_services()
            print(f"   ✅ 获取到 {len(douyin_services)} 个抖音相关服务")
            
            if douyin_services:
                print("   抖音服务示例:")
                for service in douyin_services[:3]:
                    print(f"   - ID: {service.get('id')}, 名称: {service.get('name')}, 价格: {service.get('price')}")
        except Exception as e:
            print(f"   ❌ 获取抖音服务失败: {e}")
        
        # 测试获取余额
        print("\n4. 测试获取账户余额...")
        try:
            balance = await appfuwu_client.get_balance()
            print(f"   ✅ 账户余额: ${balance}")
        except Exception as e:
            print(f"   ❌ 获取余额失败: {e}")
        
        print("\n✅ API设置功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭客户端
        await appfuwu_client.close()

if __name__ == "__main__":
    asyncio.run(test_api_settings())
