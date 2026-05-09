# 🤖 AI增强漏洞扫描系统 - Git协作指南

## 📌 重要说明

### **AI记忆的Git策略**

以下文件**已加入 `.gitignore`**，不会提交到Git仓库：

```
knowledge_base.json      # AI知识库
ai_memory_db/            # 向量数据库
@*_bounty/               # 扫描结果目录
```

---

## 🎯 别人拉取你的项目后

### **情况1：从GitHub/GitLab拉取（推荐）**

```bash
git clone https://github.com/yourname/scan.git
cd scan
pip install -r requirements.txt
```

**状态：**
- ✅ 代码完整（包括AI引擎）
- ❌ **没有AI记忆**（从零开始）
- 🆕 首次扫描时会自动创建记忆文件

**为什么这样设计？**
1. **隐私保护** - 你的扫描数据可能包含敏感信息
2. **个性化** - 每个人的使用场景不同
3. **避免冲突** - 多人同时修改会产生Git冲突
4. **文件大小** - 向量数据库可能很大

---

## 🔄 如何共享AI记忆（可选）

如果团队成员想共享AI的学习成果，有以下几种方式：

### **方式1：手动分享记忆文件（简单）**

```bash
# 成员A导出记忆
python manage_memory.py
# 选择 "2. 备份记忆"
# 生成: ai_memory_backup_20260509_143000/

# 压缩并分享给团队成员
tar -czf ai_memory_backup.tar.gz ai_memory_backup_20260509_143000/

# 成员B恢复记忆
tar -xzf ai_memory_backup.tar.gz
python manage_memory.py
# 选择 "3. 恢复记忆"
# 输入: ai_memory_backup_20260509_143000
```

### **方式2：使用共享存储（团队推荐）**

在公司内部服务器或云存储上维护一个共享的记忆库：

```bash
# 从共享位置下载最新记忆
wget http://internal-server/ai_knowledge/latest_memory.tar.gz
tar -xzf latest_memory.tar.gz

# 恢复到项目
python manage_memory.py -> 选择 "3. 恢复记忆"
```

### **方式3：定期同步脚本（自动化）**

创建 `sync_memory.sh`（Linux/Mac）或 `sync_memory.bat`（Windows）：

```bash
#!/bin/bash
# sync_memory.sh - 从服务器同步AI记忆

SERVER="http://your-server/ai-memory/"
BACKUP_FILE="latest_memory.tar.gz"

echo "正在下载最新AI记忆..."
wget -q ${SERVER}${BACKUP_FILE}

echo "正在恢复记忆..."
tar -xzf ${BACKUP_FILE}
python manage_memory.py <<< "3
ai_memory_backup_latest"

echo "✅ 记忆同步完成！"
```

---

## 📊 不同场景的对比

| 场景 | AI记忆状态 | 准确率 | 建议 |
|------|-----------|--------|------|
| **全新克隆** | 从零开始 | ~60% | 多提供反馈，快速学习 |
| **使用自己的旧记忆** | 完整保留 | 85%+ | 继续积累 |
| **导入团队记忆** | 共享知识 | 75-90% | 适合新项目 |
| **混合模式** | 个人+团队 | 90%+ | 最佳实践 |

---

## 💡 最佳实践建议

### **个人使用**
```bash
# 1. 克隆项目
git clone <repo>

# 2. 安装依赖
pip install -r requirements.txt

# 3. 开始扫描（AI从零学习）
python automate_scan.py

# 4. 定期备份记忆
python manage_memory.py -> 选择 "2. 备份记忆"
```

### **团队协作**
```bash
# 方案A：各自学习（推荐小团队）
# 每个人从零开始，根据自己的目标学习

# 方案B：共享基础记忆（推荐大团队）
# 1. 维护一个"基础记忆库"（常见漏洞模式）
# 2. 新成员导入基础记忆
# 3. 然后各自继续学习

# 方案C：中央服务器（企业级）
# 1. 搭建内部记忆服务器
# 2. 所有人定期同步
# 3. 集体智慧，越用越聪明
```

---

## 🔐 安全注意事项

### **不要提交到Git的内容：**
- ❌ `knowledge_base.json` - 可能包含敏感域名
- ❌ `ai_memory_db/` - 包含扫描详情
- ❌ `@*_bounty/` - 包含漏洞报告

### **可以提交的内容：**
- ✅ 所有代码文件
- ✅ `requirements.txt`
- ✅ 配置文件模板（不含密钥）
- ✅ 文档和示例

---

## 🚀 快速上手流程

### **新用户（从零开始）**

```bash
# 1. 克隆项目
git clone https://github.com/yourname/scan.git
cd scan

# 2. 安装依赖
pip install -r requirements.txt
# 首次运行会自动下载AI模型（约400MB）

# 3. 添加目标
echo "https://example.com" > urls/test.txt

# 4. 运行扫描
python automate_scan.py

# 5. 查看结果
ls -d @*_bounty

# 6. 训练AI（可选但推荐）
python ai_feedback.py
```

### **老用户（恢复记忆）**

```bash
# 1. 克隆项目
git clone https://github.com/yourname/scan.git
cd scan

# 2. 恢复之前的记忆
# 从备份中复制 knowledge_base.json 和 ai_memory_db/

# 3. 验证记忆状态
python manage_memory.py -> 选择 "1. 查看记忆状态"

# 4. 继续使用
python automate_scan.py
```

---

## ❓ 常见问题

### Q1: 为什么不把记忆提交到Git？
**A:** 
- 隐私问题：可能包含敏感域名和漏洞信息
- 文件大小：向量数据库可能达到几百MB
- 频繁变更：每次扫描都会更新，产生大量commit
- 个性化需求：不同用户有不同的学习目标

### Q2: 换电脑后怎么办？
**A:** 
1. 在新电脑上克隆项目
2. 从旧电脑复制 `knowledge_base.json` 和 `ai_memory_db/`
3. 或者从备份恢复

### Q3: 团队如何共享学习成果？
**A:** 
- 小团队：定期导出/导入记忆文件
- 大团队：搭建内部记忆服务器
- 或者各自学习，只在必要时分享特定案例

### Q4: 记忆文件丢失了怎么办？
**A:** 
- 不用担心，AI会从零重新开始学习
- 如果有备份，可以恢复
- 建议定期备份重要记忆

### Q5: 可以合并多个人的记忆吗？
**A:** 
- 目前不支持自动合并
- 可以手动选择一个作为基础
- 未来版本可能会支持记忆合并功能

---

## 📝 总结

| 项目 | 说明 |
|------|------|
| **Git拉取后** | AI记忆从零开始 |
| **原因** | 隐私、个性化、避免冲突 |
| **共享方式** | 手动导出/导入记忆文件 |
| **推荐做法** | 个人学习 + 定期备份 |
| **团队协作** | 共享基础记忆或各自学习 |

**记住：AI记忆是你的个人资产，就像你的笔记一样，应该由你控制何时分享！** 🧠✨
