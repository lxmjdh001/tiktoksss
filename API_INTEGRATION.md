# APPFUWU API 集成说明

## 🔄 API 更新完成

已成功将项目中的API客户端从 `shangfen622.info` 更新为 `appfuwu.icu`。

### 📋 主要变更

1. **API基础URL**: `https://appfuwu.icu/api/v2`
2. **数据库键名**: `appfuwu_api_key` (原: `shangfen_api_key`)
3. **User-Agent**: 更新为 `Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)`

### 🛠️ 支持的API功能

根据 [https://appfuwu.icu/api](https://appfuwu.icu/api) 文档，现在支持以下功能：

#### 基础功能
- ✅ 获取服务列表 (`services`)
- ✅ 获取账户余额 (`balance`)
- ✅ 提交订单 (`add`)
- ✅ 查询订单状态 (`status`)

#### 高级功能
- ✅ 批量查询订单状态 (`multi_status`)
- ✅ 创建补单 (`refill`)
- ✅ 批量创建补单 (`multi_refill`)
- ✅ 查询补单状态 (`refill_status`)
- ✅ 批量查询补单状态 (`multi_refill_status`)
- ✅ 取消订单 (`cancel`)

### 🔧 使用方法

#### 1. 设置API密钥
```python
await appfuwu_client.set_api_key("your_api_key_here")
```

#### 2. 获取服务列表
```python
services = await appfuwu_client.get_services()
douyin_services = await appfuwu_client.get_douyin_services()
```

#### 3. 提交订单
```python
result = await appfuwu_client.submit_order(
    service_id=1,
    link="https://example.com",
    quantity=100
)
```

#### 4. 查询订单状态
```python
status = await appfuwu_client.get_order_status("order_id")
```

### 🧪 测试

运行测试脚本验证API集成：

```bash
cd /Users/chaoteng/Desktop/7c/tiktok/python_backend
source venv/bin/activate
python test_appfuwu_api.py
```

### 📊 API响应格式

#### 服务列表响应
```json
[
    {
        "service": 1,
        "name": "Followers",
        "type": "Default",
        "category": "First Category",
        "rate": "0.90",
        "min": "50",
        "max": "10000",
        "refill": true,
        "cancel": true
    }
]
```

#### 订单提交响应
```json
{
    "order": 23501
}
```

#### 订单状态响应
```json
{
    "charge": "0.27819",
    "start_count": "3572",
    "status": "Partial",
    "remains": "157",
    "currency": "USD"
}
```

### ⚠️ 注意事项

1. **API密钥**: 需要先在 [https://appfuwu.icu](https://appfuwu.icu) 注册并获取API密钥
2. **SSL验证**: 当前禁用了SSL验证，生产环境建议启用
3. **服务筛选**: 抖音服务筛选基于关键词匹配，可能需要根据实际API响应调整
4. **错误处理**: 所有API调用都包含完整的错误处理机制

### 🔄 下一步

1. 设置有效的API密钥
2. 测试所有API功能
3. 根据实际API响应调整服务筛选逻辑
4. 在生产环境中启用SSL验证
