"""
APPFUWU API 客户端
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from app.database import SessionLocal
from sqlalchemy import text
import json

class AppFuwuClient:
    """APPFUWU API 客户端"""
    
    def __init__(self):
        self.base_url = "https://appfuwu.icu/api/v2"
        self.api_key = None
        # 创建HTTP客户端，禁用SSL验证
        self.client = httpx.AsyncClient(
            timeout=30.0,
            verify=False,  # 禁用SSL验证
            headers={"User-Agent": "Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)"}
        )
        
    async def get_api_key(self) -> Optional[str]:
        """从数据库获取API密钥"""
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT setting_value FROM settings WHERE setting_key = 'appfuwu_api_key'"))
            row = result.fetchone()
            return row[0] if row else None
        finally:
            db.close()
    
    async def set_api_key(self, api_key: str):
        """设置API密钥到数据库"""
        db = SessionLocal()
        try:
            db.execute(text("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value, description, updated_at) 
                VALUES ('appfuwu_api_key', :api_key, 'APPFUWU API密钥', datetime('now'))
            """), {"api_key": api_key})
            db.commit()
            self.api_key = api_key
        finally:
            db.close()
    
    async def _make_request(self, action: str, data: Dict = None) -> Dict:
        """发送API请求"""
        if not self.api_key:
            self.api_key = await self.get_api_key()
        
        if not self.api_key:
            raise Exception("API密钥未设置")
        
        # 构建POST数据
        post_data = {
            "key": self.api_key,
            "action": action
        }
        
        # 添加额外数据
        if data:
            post_data.update(data)
        
        # 转换为URL编码格式
        form_data = "&".join([f"{key}={value}" for key, value in post_data.items()])
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)"
        }
        
        try:
            response = await self.client.post(
                self.base_url, 
                headers=headers, 
                content=form_data,
                follow_redirects=True
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"API请求失败: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"请求失败: {str(e)}")
    
    async def get_services(self) -> List[Dict]:
        """获取服务列表"""
        response = await self._make_request("services")
        return response if isinstance(response, list) else []
    
    async def get_services_by_platform(self) -> Dict[str, List[Dict]]:
        """根据平台分类获取服务 - 只显示指定平台"""
        services = await self.get_services()
        platform_services = {
            "douyin": [],      # 抖音
            "xiaoshou": [],    # 快手
            "hudie": [],       # 微信
            "weibo": [],       # 微博
            "xiaohongshu": [], # 小红薯
            "meituan": []      # 美团
        }
        
        for service in services:
            service_name = service.get("name", "").lower()
            category = service.get("category", "").lower()
            formatted_service = self._format_service(service)
            
            # 抖音分类
            if any(keyword in service_name for keyword in ["douyin", "抖音", "抖吧"]):
                platform_services["douyin"].append(formatted_service)
            
            # 快手分类
            elif any(keyword in service_name for keyword in ["kuaishou", "快手", "小手"]):
                platform_services["xiaoshou"].append(formatted_service)
            
            # 微信分类（只包含真正的微信服务）
            elif any(keyword in service_name for keyword in ["wechat", "weixin", "微信"]):
                platform_services["hudie"].append(formatted_service)
            
            # 微博分类
            elif any(keyword in service_name for keyword in ["weibo", "微博", "sina"]):
                platform_services["weibo"].append(formatted_service)
            
            # 小红书分类
            elif any(keyword in service_name for keyword in ["xiaohongshu", "小红书", "小红薯", "xhs"]):
                platform_services["xiaohongshu"].append(formatted_service)
            
            # 美团分类
            elif any(keyword in service_name for keyword in ["meituan", "美团", "meituan", "外卖", "dianping", "大众点评"]):
                platform_services["meituan"].append(formatted_service)
            
            # 其他平台（tiktok, facebook等）不显示，直接跳过
            # 如果都不匹配，也不显示
            else:
                pass  # 跳过不显示
        
        return platform_services

    async def get_douyin_services(self) -> List[Dict]:
        """获取抖音相关服务（保持向后兼容）"""
        platform_services = await self.get_services_by_platform()
        return platform_services["douyin"]
    
    async def submit_order(self, service_id: int, link: str, quantity: int, order_type: str = "fixed", comments: str = None) -> Dict:
        """提交订单"""
        data = {
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        
        # 如果是真人评论服务，添加评论内容参数
        if comments:
            data["comments"] = comments
        
        response = await self._make_request("add", data)
        
        # 确保返回格式包含success字段
        if isinstance(response, dict):
            if "order" in response:
                return {
                    "success": True,
                    "order_id": response.get("order"),
                    "message": "订单提交成功"
                }
            else:
                return {
                    "success": False,
                    "message": response.get("error", "订单提交失败")
                }
        else:
            return {
                "success": False,
                "message": "API响应格式错误"
            }
    
    async def get_order_status(self, order_id: str) -> Dict:
        """查询订单状态"""
        data = {"order": order_id}
        response = await self._make_request("status", data)
        return response
    
    async def get_balance(self) -> float:
        """获取账户余额"""
        response = await self._make_request("balance")
        return float(response.get("balance", 0))
    
    async def refill_order(self, order_id: int) -> Dict:
        """创建补单"""
        data = {"order": order_id}
        response = await self._make_request("refill", data)
        return response
    
    async def multi_refill_orders(self, order_ids: List[int]) -> Dict:
        """批量创建补单"""
        data = {"orders": ",".join(map(str, order_ids))}
        response = await self._make_request("refill", data)
        return response
    
    async def get_refill_status(self, refill_id: int) -> Dict:
        """获取补单状态"""
        data = {"refill": refill_id}
        response = await self._make_request("refill_status", data)
        return response
    
    async def multi_refill_status(self, refill_ids: List[int]) -> Dict:
        """批量获取补单状态"""
        data = {"refills": ",".join(map(str, refill_ids))}
        response = await self._make_request("refill_status", data)
        return response
    
    async def cancel_orders(self, order_ids: List[int]) -> Dict:
        """取消订单"""
        data = {"orders": ",".join(map(str, order_ids))}
        response = await self._make_request("cancel", data)
        return response
    
    async def multi_order_status(self, order_ids: List[int]) -> Dict:
        """批量查询订单状态"""
        data = {"orders": ",".join(map(str, order_ids))}
        response = await self._make_request("status", data)
        return response
    
    def _format_service(self, service: Dict) -> Dict:
        """格式化服务数据"""
        service_name = service.get("name", "")
        
        return {
            "id": service.get("service"),
            "name": service_name,
            "type": service.get("type", ""),
            "price": float(service.get("rate", 0)),
            "min_quantity": int(service.get("min", 1)),
            "max_quantity": int(service.get("max", 10000)),
            "recharge": service.get("refill", False),
            "cancel": service.get("cancel", False)
        }
    
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

# 全局客户端实例
appfuwu_client = AppFuwuClient()
