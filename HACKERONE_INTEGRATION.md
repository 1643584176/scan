# HackerOne API 集成使用指南

## 📋 功能说明

本模块可以自动从 HackerOne 获取你的漏洞赏金项目目标范围，并自动开始扫描。

## 🔧 配置步骤

### 1. 获取 API Token

1. 登录 HackerOne
2. 访问 https://hackerone.com/settings/api_token
3. 点击 "Generate new token"
4. 复制生成的 Token

### 2. 设置环境变量

**Windows (PowerShell):**
```powershell
$env:HACKERONE_API_TOKEN="your_api_token_here"
$env:HACKERONE_USERNAME="your_username_here"
```

**Windows (CMD):**
```cmd
set HACKERONE_API_TOKEN=your_api_token_here
set HACKERONE_USERNAME=your_username_here
```

**Linux/Mac:**
```bash
export HACKERONE_API_TOKEN="your_api_token_here"
export HACKERONE_USERNAME="your_username_here"
```

### 3. 永久设置（可选）

**Windows:**
1. 右键"此电脑" → 属性 → 高级系统设置
2. 点击"环境变量"
3. 在"用户变量"中添加：
   - `HACKERONE_API_TOKEN` = 你的 Token
   - `HACKERONE_USERNAME` = 你的用户名

**Linux/Mac:**
将以下内容添加到 `~/.bashrc` 或 `~/.zshrc`:
```bash
export HACKERONE_API_TOKEN="your_api_token_here"
export HACKERONE_USERNAME="your_username_here"
```

## 🚀 使用方法

### 自动获取目标并扫描

```bash
python automate_scan.py
```

脚本会：
1. 检查 HackerOne API 配置
2. 如果配置了，自动获取你的项目目标
3. 将目标保存到 `urls/hackerone_targets.txt`
4. 开始扫描这些目标

### 手动测试 API

```bash
python tools/hackerone_api.py
```

这会测试 API 连接并显示：
- 你参与的项目列表
- 每个项目的目标域名
- 最近的漏洞报告

## 📊 API 功能

### 1. 获取项目列表
```python
from tools.hackerone_api import HackerOneAPI

client = HackerOneAPI()
programs = client.get_programs()
for program in programs:
    print(program['attributes']['name'])
```

### 2. 获取目标范围
```python
# 获取指定项目的域名
domains = client.get_in_scope_domains('shopify')
print(f"找到 {len(domains)} 个域名")
```

### 3. 创建漏洞报告
```python
report = client.create_report(
    program_handle='shopify',
    title='XSS Vulnerability in Search',
    vulnerability_type='XSS',
    severity='high',
    description='Found reflected XSS...',
    impact='An attacker can...',
    steps_to_reproduce='1. Go to...\n2. Input...',
    urls=['https://example.com/search?q=<script>']
)
print(f"报告创建成功: {report['id']}")
```

### 4. 获取报告列表
```python
# 获取所有报告
reports = client.get_reports()

# 获取特定状态的报告
new_reports = client.get_reports(status='new')
```

## 🔒 安全提示

1. **不要泄露 API Token**
   - Token 已经在 `.gitignore` 中
   - 不要上传到 GitHub
   - 不要分享给他人

2. **权限控制**
   - API Token 只有读取权限
   - 不会修改你的账户信息
   - 只能访问你有权限的项目

3. **速率限制**
   - HackerOne API 有速率限制
   - 避免频繁调用
   - 脚本已做优化

## ❓ 常见问题

### Q: 如何知道 API Token 是否正确？
A: 运行 `python tools/hackerone_api.py`，如果能看到项目列表说明正确。

### Q: 可以只扫描特定项目吗？
A: 可以，修改 `load_targets_from_hackerone(['project1', 'project2'])`

### Q: API 会暴露我的漏洞报告吗？
A: 不会，只能获取你自己提交的报告和公开信息。

### Q: 如果不想用 HackerOne 集成怎么办？
A: 不设置环境变量即可，脚本会自动跳过，使用本地目标文件。

## 📝 示例输出

```
[INFO] 检查 HackerOne API 配置...
[INFO] 发现 HackerOne 配置，正在获取目标范围...
[INFO] 获取项目 shopify 的目标范围...
[OK] shopify: 找到 15 个域名
[INFO] 获取项目 uber 的目标范围...
[OK] uber: 找到 8 个域名
[OK] 从 HackerOne 获取到 23 个目标
[OK] 目标已保存到: urls/hackerone_targets.txt

[INFO] 检查工具更新...
...
```

## 🎯 下一步

配置完成后，直接运行：
```bash
python automate_scan.py
```

脚本会自动：
1. 从 HackerOne 获取目标
2. 对每个目标进行完整扫描
3. 生成详细的扫描报告

祝你挖洞愉快！🎉
