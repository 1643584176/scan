# 🤖 AI增强版漏洞扫描系统

> **社区共享 · 集体智慧 · 互帮互助**

[English](#english) | [社区共享说明](社区共享说明.md) | [AI使用指南](AI使用指南.md)

---

## ✨ 核心特性

- 🧠 **AI智能分析** - 自动识别真实漏洞和误报
- 📚 **记忆系统** - 记住历史案例，跨项目复用
- 🌍 **社区共享** - 贡献经验，获取全球智慧
- 🔄 **自学习进化** - 越用越智能，准确率持续提升
- 🔒 **完全本地化** - 数据隐私安全，离线可用

---

## 🚀 快速开始（3步）

### **方式1：新用户（推荐）**

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载Nuclei工具
python tools/setup_tools.py
# 或查看 tools/nuclei/INSTALL.md

# 3. 一键导入示例社区智慧
python quick_start.py

# 4. 开始扫描
python automate_scan.py
```

### **方式2：手动操作**

1. 安装Python依赖：`pip install -r requirements.txt`
2. 将目标URL放入 `urls/` 目录的文本文件中，每行一个URL
3. 运行 `python automate_scan.py` 开始AI增强扫描
4. （可选）运行 `python share_memory.py` 贡献经验或下载社区智慧

---

## 🌍 社区共享 - 互帮互助

### **核心理念**
你的每一次扫描都在为社区贡献智慧，其他人的经验也会帮助你！

### **参与方式**

```bash
# 贡献你的经验（匿名）
python share_memory.py

# 下载社区智慧
python share_memory.py

# 导入到本地AI
python import_community.py
```

**效果：**
- 📈 准确率从60%提升到85%+
- 🎯 立即识别罕见漏洞类型
- 🤝 与全球用户共同成长

详见：[社区共享说明.md](社区共享说明.md)

---

## 📁 目录结构

### **核心文件**
- **automate_scan.py** - AI增强版主扫描脚本
- **ai_analyzer.py** - AI智能分析引擎
- **ai_feedback.py** - 反馈学习工具
- **share_memory.py** - 社区共享系统
- **import_community.py** - 导入社区智慧
- **manage_memory.py** - 记忆管理工具
- **quick_start.py** - 快速开始向导

### **数据文件**
- **knowledge_base.json** - 本地AI知识库（不提交Git）
- **ai_memory_db/** - 向量数据库（不提交Git）
- **example_community_wisdom.json** - 示例社区智慧

### **文档**
- **README.md** - 项目说明
- **AI使用指南.md** - 详细使用手册
- **社区共享说明.md** - 共享系统说明
- **GIT协作指南.md** - Git协作说明

### **其他**
- **common/** - 共享资源（漏洞模式、排除项）
- **example_bounty/** - 赏金项目模板
- **tools/** - 扫描工具（Nuclei、Wappalyzer等）
- **urls/** - URL输入目录

---

## English

# 🤖 AI-Enhanced Vulnerability Scanner

> **Community Sharing · Collective Wisdom · Mutual Help**

## ✨ Features

- 🧠 **AI Analysis** - Automatically identify real vulnerabilities and false positives
- 📚 **Memory System** - Remember historical cases, cross-project reuse
- 🌍 **Community Sharing** - Contribute experience, gain global wisdom
- 🔄 **Self-Learning** - Smarter with use, accuracy continuously improves
- 🔒 **Fully Local** - Data privacy secure, offline available

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Import example community wisdom
python quick_start.py

# 3. Start scanning
python automate_scan.py
```

## 🌍 Community Sharing

Contribute your scanning experience (anonymized) and download community wisdom:

```bash
python share_memory.py      # Contribute or download
python import_community.py  # Import to local AI
```

See: [社区共享说明.md](社区共享说明.md) (Chinese)

## Directory Structure

- **automate_scan.py** - Main AI-enhanced scanning script
- **ai_analyzer.py** - AI analysis engine
- **share_memory.py** - Community sharing system
- **knowledge_base.json** - Local AI knowledge base (not in Git)
- **example_community_wisdom.json** - Example community wisdom
- **tools/** - Scanning tools (Nuclei, Wappalyzer, etc.)
- **urls/** - URL input directory
