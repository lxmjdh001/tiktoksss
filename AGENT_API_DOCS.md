# 代理API接口文档

## 📋 接口概览

| 接口 | 方法 | 路径 | 描述 |
|------|------|------|------|
| 生成二维码 | GET | `/agent/qrcode` | 生成邀请二维码 |
| 获取统计信息 | GET | `/agent/stats` | 获取代理统计信息 |
| 获取邀请用户 | GET | `/agent/invitees` | 获取邀请用户列表 |
| 获取返佣记录 | GET | `/agent/commissions` | 获取返佣记录 |

## 🔐 认证要求

所有接口都需要用户登录，通过Session进行身份验证。

## 📖 接口详情

### 1. 生成邀请二维码

**接口地址**: `GET /agent/qrcode`

**功能描述**: 生成用户的专属邀请二维码

**请求参数**: 无

**响应示例**:
```json
{
    "success": true,
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "invite_link": "https://example.com/auth/register?invite_code=ABC12345"
}
```

**响应字段说明**:
- `success`: 请求是否成功
- `qr_code`: Base64编码的二维码图片
- `invite_link`: 邀请链接

---

### 2. 获取代理统计信息

**接口地址**: `GET /agent/stats`

**功能描述**: 获取代理的统计信息

**请求参数**: 无

**响应示例**:
```json
{
    "success": true,
    "stats": {
        "total_invitees": 15,
        "active_invitees": 8,
        "total_commission": 1250.50,
        "monthly_commission": 320.75,
        "total_consumption": 12500.00
    },
    "user_info": {
        "id": 123,
        "username": "agent_user",
        "email": "agent@example.com",
        "invite_code": "ABC12345",
        "is_agent": true,
        "agent_level": 1,
        "direct_commission_rate": 0.10,
        "indirect_commission_rate": 0.05
    }
}
```

**响应字段说明**:
- `stats.total_invitees`: 总邀请用户数
- `stats.active_invitees`: 活跃邀请用户数
- `stats.total_commission`: 总返佣金额
- `stats.monthly_commission`: 本月返佣金额
- `stats.total_consumption`: 总下级消费金额
- `user_info`: 用户基本信息

---

### 3. 获取邀请用户列表

**接口地址**: `GET /agent/invitees`

**功能描述**: 获取邀请的用户列表

**请求参数**:
- `page` (可选): 页码，默认1
- `limit` (可选): 每页数量，默认10

**响应示例**:
```json
{
    "success": true,
    "invitees": [
        {
            "id": 456,
            "username": "invited_user1",
            "email": "user1@example.com",
            "is_agent": false,
            "agent_level": 0,
            "created_at": "2024-01-15T10:30:00",
            "total_orders": 5,
            "total_consumed": 500.00,
            "total_commission": 50.00
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 10,
        "total": 15,
        "pages": 2
    }
}
```

**响应字段说明**:
- `invitees`: 邀请用户列表
- `pagination`: 分页信息

---

### 4. 获取返佣记录

**接口地址**: `GET /agent/commissions`

**功能描述**: 获取返佣记录列表

**请求参数**:
- `page` (可选): 页码，默认1
- `limit` (可选): 每页数量，默认10

**响应示例**:
```json
{
    "success": true,
    "commissions": [
        {
            "id": 789,
            "commission_type": "direct",
            "commission_rate": 0.10,
            "order_amount": 100.00,
            "commission_amount": 10.00,
            "status": "paid",
            "created_at": "2024-01-15T10:30:00",
            "paid_at": "2024-01-16T09:00:00",
            "consumer": {
                "id": 456,
                "username": "invited_user1",
                "email": "user1@example.com"
            },
            "order": {
                "id": 1001,
                "service_name": "抖音点赞",
                "quantity": 100
            }
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 10,
        "total": 25,
        "pages": 3
    }
}
```

**响应字段说明**:
- `commissions`: 返佣记录列表
- `commission_type`: 返佣类型 (direct/indirect)
- `status`: 状态 (pending/paid/cancelled)
- `consumer`: 消费者信息
- `order`: 订单信息

## 🚨 错误响应

**未登录错误**:
```json
{
    "detail": "未登录"
}
```

**权限不足错误**:
```json
{
    "detail": "权限不足"
}
```

## 📝 使用示例

### JavaScript调用示例

```javascript
// 生成二维码
async function generateQRCode() {
    const response = await fetch('/agent/qrcode');
    const result = await response.json();
    
    if (result.success) {
        document.getElementById('qrCodeImage').src = result.qr_code;
    }
}

// 获取统计信息
async function getStats() {
    const response = await fetch('/agent/stats');
    const result = await response.json();
    
    if (result.success) {
        console.log('总邀请用户:', result.stats.total_invitees);
        console.log('总返佣:', result.stats.total_commission);
    }
}

// 获取邀请用户列表
async function getInvitees(page = 1) {
    const response = await fetch(`/agent/invitees?page=${page}&limit=20`);
    const result = await response.json();
    
    if (result.success) {
        console.log('邀请用户:', result.invitees);
        console.log('分页信息:', result.pagination);
    }
}
```

### Python调用示例

```python
import requests

# 设置session
session = requests.Session()
session.cookies.set('session_id', 'your_session_id')

# 生成二维码
response = session.get('http://localhost:8000/agent/qrcode')
result = response.json()

if result['success']:
    qr_code = result['qr_code']
    invite_link = result['invite_link']
    print(f"邀请链接: {invite_link}")

# 获取统计信息
response = session.get('http://localhost:8000/agent/stats')
result = response.json()

if result['success']:
    stats = result['stats']
    print(f"总邀请用户: {stats['total_invitees']}")
    print(f"总返佣: {stats['total_commission']}")
```

## 🔧 技术说明

- **认证方式**: Session-based认证
- **数据格式**: JSON
- **分页**: 支持page和limit参数
- **错误处理**: 统一的错误响应格式
- **性能优化**: 数据库查询优化，支持分页
