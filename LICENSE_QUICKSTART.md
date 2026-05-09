# 🔑 许可证系统 - 快速参考

## 📌 一分钟了解

**你想控制谁能使用共享记忆功能？**

✅ **可以！** 通过许可证系统实现。

---

## 🚀 三步设置

### **1️⃣ 生成许可证（你）**

```bash
python license_manager.py
# 选择 "3. 生成许可证密钥"
# 输入密码: admin123（首次使用）
# 选择类型: basic/professional/enterprise
```

**你会得到：**
```
YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY3ODkw...
```

### **2️⃣ 发送给用户**

复制密钥，通过微信/QQ/邮件发送给用户。

### **3️⃣ 用户激活**

用户运行：
```bash
python license_manager.py
# 选择 "1. 激活许可证"
# 粘贴密钥
```

**完成！** ✅

---

## 💰 定价建议

| 版本 | 价格 | 功能 | 有效期 |
|------|------|------|--------|
| 试用版 | 免费 | 仅下载 | 7天 |
| 基础版 | ¥99/年 | 共享+下载 | 365天 |
| 专业版 | ¥299/年 | 全部功能 | 365天 |
| 企业版 | ¥999 | 全部功能+支持 | 永久 |

---

## 🎯 常见场景

### **场景1：新用户想试试**
```bash
# 生成试用版（7天）
python license_manager.py -> 3
类型: trial
天数: 7
```

### **场景2：用户付费购买**
```bash
# 生成基础版（1年）
python license_manager.py -> 3
类型: basic
天数: 365
```

### **场景3：团队多设备**
```bash
# 生成企业版（允许5次激活）
python license_manager.py -> 3
类型: enterprise
最大激活次数: 5
```

---

## 🔒 安全设置

### **修改管理员密码**
编辑 `license_manager.py` 第328行：
```python
if password == "你的新密码":
```

### **修改签名密钥**
编辑 `license_manager.py` 第144行和第185行：
```python
secret = "随机字符串_越复杂越好"
```

---

## 📊 管理命令

```bash
# 查看许可证状态
python license_manager.py -> 2

# 停用许可证
python license_manager.py -> 4

# 演示完整流程
python demo_license.py
```

---

## ❓ 常见问题

**Q: 如何防止破解？**
A: 数字签名 + 硬件绑定 + 代码混淆

**Q: 用户如何续费？**
A: 生成新密钥，用户重新激活

**Q: 可以退款吗？**
A: 运行 `python license_manager.py` 选择 "4. 停用"

**Q: 密钥泄露怎么办？**
A: 限制激活次数，每个用户唯一密钥

---

## 📞 需要帮助？

查看详细文档：[许可证系统说明.md](许可证系统说明.md)

---

**就这么简单！开始控制你的共享功能吧！** 🎉
