# 代理返佣系统设计

## 🎯 **系统概述**

实现了完整的多级代理返佣系统，支持邀请关系和自动返佣计算。

## 📊 **数据库设计**

### **用户表新增字段**
```sql
-- 邀请关系
inviter_id INTEGER REFERENCES users(id)  -- 邀请人ID
invite_code VARCHAR(20) UNIQUE          -- 邀请码

-- 代理信息
is_agent BOOLEAN DEFAULT 0              -- 是否为代理
agent_level INTEGER DEFAULT 0           -- 代理等级

-- 返佣比例
direct_commission_rate DECIMAL(5,4)     -- 直接邀请返佣比例
indirect_commission_rate DECIMAL(5,4)   -- 间接邀请返佣比例

-- 返佣统计
total_direct_commission DECIMAL(10,2)   -- 直接邀请总返佣
total_indirect_commission DECIMAL(10,2) -- 间接邀请总返佣
total_commission DECIMAL(10,2)          -- 总返佣
```

### **返佣记录表**
```sql
CREATE TABLE commission_records (
    id INTEGER PRIMARY KEY,
    agent_id INTEGER NOT NULL,           -- 代理ID
    consumer_id INTEGER NOT NULL,        -- 消费者ID
    order_id INTEGER NOT NULL,           -- 订单ID
    commission_type VARCHAR(20),         -- 返佣类型: direct/indirect
    commission_rate DECIMAL(5,4),        -- 返佣比例
    order_amount DECIMAL(10,4),          -- 订单金额
    commission_amount DECIMAL(10,4),     -- 返佣金额
    status VARCHAR(20) DEFAULT 'pending', -- 状态: pending/paid/cancelled
    created_at DATETIME,
    paid_at DATETIME
);
```

### **返佣配置表**
```sql
CREATE TABLE commission_configs (
    id INTEGER PRIMARY KEY,
    agent_level INTEGER NOT NULL,        -- 代理等级
    direct_rate DECIMAL(5,4),            -- 直接邀请返佣比例
    indirect_rate DECIMAL(5,4),          -- 间接邀请返佣比例
    max_levels INTEGER DEFAULT 3,        -- 最大返佣层级
    is_active BOOLEAN DEFAULT 1,         -- 是否启用
    description TEXT                     -- 描述
);
```

## 🔄 **返佣流程**

### **1. 邀请关系建立**
```
A用户(代理) → 邀请B用户 → B用户注册时填写A的邀请码
B用户(代理) → 邀请C用户 → C用户注册时填写B的邀请码
```

### **2. 返佣计算**
```
C用户消费 → 系统自动计算返佣：
- B用户(直接邀请) → 获得直接返佣
- A用户(间接邀请) → 获得间接返佣
```

### **3. 返佣层级**
- **直接邀请**: 1级返佣 (B邀请C，B获得直接返佣)
- **间接邀请**: 2级返佣 (A邀请B，B邀请C，A获得间接返佣)
- **最大层级**: 可配置，默认3级

## 💰 **返佣比例配置**

### **默认配置**
| 代理等级 | 直接返佣 | 间接返佣 | 说明 |
|---------|---------|---------|------|
| 1级代理 | 10% | 5% | 一级代理：直接邀请10%，间接邀请5% |
| 2级代理 | 15% | 8% | 二级代理：直接邀请15%，间接邀请8% |
| 3级代理 | 20% | 10% | 三级代理：直接邀请20%，间接邀请10% |

## 🛠️ **核心功能**

### **1. 代理管理**
- 设置用户为代理
- 配置返佣比例
- 查看代理统计

### **2. 邀请码系统**
- 自动生成唯一邀请码
- 支持邀请码注册
- 邀请关系追踪

### **3. 返佣计算**
- 订单完成后自动计算返佣
- 支持多级返佣
- 返佣记录管理

### **4. 统计报表**
- 代理业绩统计
- 返佣记录查询
- 邀请树展示

## 📱 **API接口**

### **代理管理**
- `GET /admin/agents` - 代理管理页面
- `POST /admin/agents/set-agent` - 设置代理
- `POST /admin/agents/update-commission` - 更新返佣比例

### **返佣记录**
- `GET /admin/agents/commission-records` - 返佣记录页面
- `GET /admin/agents/commission-config` - 返佣配置页面
- `POST /admin/agents/commission-config/update` - 更新返佣配置

### **邀请树**
- `GET /admin/agents/invite-tree` - 邀请树页面

## 🔧 **使用示例**

### **设置代理**
```python
# 设置用户为1级代理
POST /admin/agents/set-agent
{
    "user_id": 123,
    "agent_level": 1,
    "direct_rate": 0.10,    # 10%
    "indirect_rate": 0.05   # 5%
}
```

### **注册邀请**
```python
# 用户注册时填写邀请码
POST /auth/register
{
    "email": "user@example.com",
    "username": "user",
    "password": "password",
    "invite_code": "ABC12345"  # 代理的邀请码
}
```

### **返佣计算**
```python
# 订单完成后自动计算返佣
order = Order(...)
commission_service = CommissionService(db)
commission_records = await commission_service.calculate_commission(order)
```

## 📈 **业务逻辑**

### **邀请链示例**
```
A(代理) → B(代理) → C(用户)
C消费100元：
- B获得直接返佣: 100 × 10% = 10元
- A获得间接返佣: 100 × 5% = 5元
```

### **返佣状态**
- **pending**: 待支付
- **paid**: 已支付
- **cancelled**: 已取消

## 🎯 **管理功能**

### **代理管理页面**
- 查看所有代理
- 设置代理等级
- 配置返佣比例
- 查看代理统计

### **返佣记录页面**
- 查看所有返佣记录
- 按代理筛选
- 按状态筛选
- 支付返佣

### **邀请树页面**
- 可视化邀请关系
- 查看邀请层级
- 统计邀请数量

## ✅ **系统特点**

1. **自动化**: 订单完成后自动计算返佣
2. **多层级**: 支持多级返佣关系
3. **可配置**: 返佣比例可灵活配置
4. **可追踪**: 完整的返佣记录和统计
5. **可视化**: 邀请树和统计报表
6. **安全**: 邀请码唯一性保证

## 🚀 **部署说明**

1. 运行数据库迁移脚本
2. 配置返佣比例
3. 设置代理用户
4. 开始使用邀请功能

系统已完全集成到现有平台，支持完整的代理返佣业务流程！
