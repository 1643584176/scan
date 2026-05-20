# HackerOne API Token 获取和配置指南

## 📋 如何获取 HackerOne API Token

### 步骤 1: 登录 HackerOne

访问 https://hackerone.com 并登录你的账户

### 步骤 2: 进入 API 设置页面

1. 点击右上角的头像
2. 选择 **"Settings"**（设置）
3. 在左侧菜单中选择 **"API Token"**
4. 或者直接访问：https://hackerone.com/settings/api_token

### 步骤 3: 生成 API Token

1. 点击 **"Generate new token"** 按钮
2. 输入 Token 描述（例如："Security Scanner"）
3. 点击 **"Generate Token"**
4. **重要**：立即复制生成的 Token，它只会显示一次！

### 步骤 4: 记录你的用户名

在 HackerOne 个人主页可以看到你的用户名，或者在 URL 中：
```
https://hackerone.com/YOUR_USERNAME
```

---

## 🔧 配置到项目中

### 方法 1: 使用 .env 文件（推荐）✅

1. 编辑项目根目录的 `.env` 文件
2. 填入你的 Token 和用户名：

```ini
# HackerOne API 配置
HACKERONE_API_TOKEN=abc123def456ghi789...
HACKERONE_USERNAME=your_username
```

3. 保存文件

**优点：**
- ✅ 配置持久化，不需要每次都设置
- ✅ 已添加到 `.gitignore`，不会泄露
- ✅ 简单易用

### 方法 2: 使用环境变量

**Windows (PowerShell):**
```powershell
$env:HACKERONE_API_TOKEN="your_token_here"
$env:HACKERONE_USERNAME="your_username_here"
python automate_scan.py
```

**Windows (CMD):**
```cmd
set HACKERONE_API_TOKEN=your_token_here
set HACKERONE_USERNAME=your_username_here
python automate_scan.py
```

**Linux/Mac:**
```bash
export HACKERONE_API_TOKEN="your_token_here"
export HACKERONE_USERNAME="your_username_here"
python automate_scan.py
```

**注意：** 这种方式只在当前终端会话有效，关闭后需要重新设置。

---

## ✅ 验证配置

### 测试 API 连接

运行以下命令测试配置是否正确：

```bash
python tools/hackerone_api.py
```

如果配置正确，你会看到：

```
HackerOne API 测试
============================================================

1. 获取项目列表...
   找到 X 个项目

2. 获取第一个项目 (xxx) 的目标范围...
   找到 X 个域名
   示例: ['example.com', 'test.com']

3. 获取最近的报告...
   找到 X 个报告
```

### 测试扫描器集成

运行扫描器：

```bash
python automate_scan.py
```

你应该看到：

```
[OK] 已加载 .env 配置文件

[INFO] 检查 HackerOne API 配置...
[INFO] 发现 HackerOne 配置，正在获取目标范围...
[INFO] 获取项目 xxx 的目标范围...
[OK] xxx: 找到 X 个域名
[OK] 从 HackerOne 获取到 X 个目标
[OK] 目标已保存到: urls/hackerone_targets.txt
```

---

## 🔒 安全提示

### ⚠️ 重要注意事项

1. **Token 保密**
   - ❌ 不要分享给任何人
   - ❌ 不要上传到 GitHub
   - ❌ 不要在公开场合展示
   - ✅ 已添加到 `.gitignore`，不会被提交

2. **权限控制**
   - API Token 只有读取权限
   - 不能修改你的账户信息
   - 只能访问你有权限的项目

3. **定期轮换**
   - 建议每 3-6 个月更换一次 Token
   - 如果怀疑泄露，立即撤销并重新生成

4. **最小权限**
   - 只授予必要的权限
   - 不要使用管理员级别的 Token

---

## ❓ 常见问题

### Q1: Token 无效怎么办？

**症状：** 出现 "401 Unauthorized" 错误

**解决：**
1. 检查 Token 是否复制完整
2. 确认没有多余的空格
3. 重新生成新的 Token
4. 确保用户名正确

### Q2: 看不到我的项目？

**可能原因：**
1. 你没有参与任何漏洞赏金项目
2. 项目设置为私有
3. API 权限不足

**解决：**
1. 确认你已加入至少一个项目
2. 联系项目管理员确认权限
3. 检查 Token 权限设置

### Q3: .env 文件会被提交到 Git 吗？

**不会！** `.env` 已经在 `.gitignore` 中，Git 会忽略它。

你可以验证：
```bash
git status
```

`.env` 不应该出现在待提交的文件列表中。

### Q4: 可以同时使用多个 Token 吗？

可以，但需要在运行时切换：

```bash
# 使用 Token 1
cp .env.token1 .env
python automate_scan.py

# 使用 Token 2
cp .env.token2 .env
python automate_scan.py
```

### Q5: 不想用 HackerOne 集成怎么办？

很简单，有两种方式：

**方式 1：** 删除或重命名 `.env` 文件
```bash
rename .env .env.bak
```

**方式 2：** 注释掉 `.env` 中的配置
```ini
# HACKERONE_API_TOKEN=xxx
# HACKERONE_USERNAME=xxx
```

扫描器会自动跳过 HackerOne 集成，使用本地目标文件。

---

## 🎯 下一步

配置完成后：

1. **测试连接**
   ```bash
   python tools/hackerone_api.py
   ```

2. **开始扫描**
   ```bash
   python automate_scan.py
   ```

3. **学习漏洞报告**
   ```bash
   python tools/vuln_report_learner.py XSS 10
   ```

---

## 📞 需要帮助？

如果遇到问题：

1. 检查 HackerOne API 文档：https://api.hackerone.com/
2. 查看项目 README.md
3. 检查日志输出中的错误信息

祝你挖洞愉快！🎉
