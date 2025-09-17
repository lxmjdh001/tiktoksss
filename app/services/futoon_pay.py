"""
富通支付对接：签名、下单、验签、查询

说明：本实现直接复用用户提供的 Django 版本的核心算法，改为独立可在 FastAPI 中调用的纯 Python 模块。
"""

from __future__ import annotations

import hashlib
import html
from typing import Dict, Any, Optional

import requests


class FutoonPayConfig:
    """运行时配置容器。建议从数据库或环境变量注入。"""

    def __init__(
        self,
        pid: str,
        key: str,
        api_url: str = "https://futoon.org/mapi.php",
        query_url: str = "https://futoon.org/api.php",
    ) -> None:
        self.pid = pid
        self.key = key
        self.api_url = api_url
        self.query_url = query_url


class FutoonPay:
    """富通支付客户端"""

    PAYMENT_TYPES = {
        "wechat": "wxpay",
        "alipay": "alipay",
    }

    def __init__(self, config: FutoonPayConfig) -> None:
        self.config = config

    # -------- 核心：签名逻辑（与用户提供版本保持一致） --------
    def generate_sign(self, params: Dict[str, Any]) -> str:
        # 过滤空值、签名字段
        sign_params: Dict[str, str] = {}
        for k, v in params.items():
            if k in ("sign", "sign_type"):
                continue
            if v is None:
                continue
            value = str(v).strip()
            if not value:
                continue
            if "&quot;" in value:
                value = html.unescape(value)
            sign_params[k] = value

        # 按参数名 ASCII 排序
        sorted_items = sorted(sign_params.items(), key=lambda x: x[0])

        # a=b&c=d&e=f + KEY
        sign_string = "&".join([f"{k}={v}" for k, v in sorted_items])
        sign_string = f"{sign_string}{self.config.key}"

        # MD5 小写
        return hashlib.md5(sign_string.encode("utf-8")).hexdigest()

    # -------- 下单 --------
    def create_order(
        self,
        *,
        out_trade_no: str,
        name: str,
        money: str | float,
        payment_type: str,
        notify_url: str,
        return_url: str,
        client_ip: str,
        param: Optional[str] = None,
        device: str = "pc",
        timeout: int = 10,
    ) -> Dict[str, Any]:
        if payment_type not in self.PAYMENT_TYPES:
            return {"success": False, "message": f"不支持的支付方式: {payment_type}"}

        params: Dict[str, Any] = {
            "pid": self.config.pid,
            "type": self.PAYMENT_TYPES[payment_type],
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "return_url": return_url,
            "name": name,
            "money": str(money),
            "clientip": client_ip,
            "device": device,
        }
        if param and str(param).strip():
            params["param"] = param

        params["sign"] = self.generate_sign(params)
        params["sign_type"] = "MD5"

        try:
            resp = requests.post(self.config.api_url, data=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # 网络或解析异常
            return {"success": False, "message": f"网络请求失败: {exc}"}

        if data.get("code") == 1:
            return {
                "success": True,
                "trade_no": data.get("trade_no"),
                "payurl": data.get("payurl"),
                "qrcode": data.get("qrcode"),
                "urlscheme": data.get("urlscheme"),
                "message": "订单创建成功",
            }
        return {"success": False, "message": data.get("msg", "订单创建失败")}

    # -------- 验签 --------
    def verify_notify(self, notify_params: Dict[str, Any]) -> bool:
        if "sign" not in notify_params:
            return False
        remote_sign = notify_params.get("sign")
        local_sign = self.generate_sign(notify_params)
        return str(remote_sign) == str(local_sign)

    # -------- 查询订单 --------
    def query_order(self, out_trade_no: str, timeout: int = 10) -> Dict[str, Any]:
        params = {
            "act": "order",
            "pid": self.config.pid,
            "key": self.config.key,
            "out_trade_no": out_trade_no,
        }
        try:
            resp = requests.get(self.config.query_url, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            return {"success": False, "message": f"网络请求失败: {exc}"}

        if data.get("code") == 1:
            return {"success": True, "order_info": data}
        return {"success": False, "message": data.get("msg", "查询失败")}


