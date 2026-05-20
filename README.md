# 🔍 智能安全扫描器

基于 Go 工具的自动化 Web 安全扫描系统，集成 HackerOne 漏洞报告学习功能。

## ✨ 核心特性

- 🚀 **快速扫描** - 使用 Go 编写的高性能工具（Nuclei, httpx, Katana）
- 🎯 **精准检测** - 智能 URL 收集和分类，减少误报
- 📖 **漏洞学习** - 从 HackerOne 公开报告学习实战技巧
- 🔧 **易于使用** - 简化的工作流程，一键扫描
- 📊 **详细报告** - 自动生成 Markdown 格式扫描报告
- 🔒 **本地运行** - 所有数据保存在本地，保护隐私

## 🚀 快速开始

### 1. 环境要求

- Python 3.7+
- Go 1.20+ （用于安装扫描工具）

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Go 扫描工具
python tools/go_tools.py install
```

### 3. 添加目标

编辑 `urls/targets.txt`，添加要扫描的目标（每行一个）：

```
https://example.com
https://test.com
```

### 4. 开始扫描

```bash
python automate_scan.py
```

扫描结果将保存在 `@域名_bounty/` 目录中。

## 📚 漏洞报告学习

### 搜索公开漏洞报告

```bash
# 搜索 XSS 报告
python tools/vuln_report_learner.py XSS

# 搜索 SQL 注入报告（10个）
python tools/vuln_report_learner.py "SQL Injection" 10

# 搜索 IDOR 报告
python tools/vuln_report_learner.py IDOR 5
```

### 查看学习报告

生成的报告会保存为 Markdown 文件：
- `xss_learning_report.md`
- `sql_injection_learning_report.md`
- 等等...

详见：[VULN_REPORT_LEARNING.md](VULN_REPORT_LEARNING.md)

## 🛠️ 工具管理

### 检查工具状态

```bash
python tools/go_tools.py check
```

### 更新工具

```bash
python tools/go_tools.py update
```

### 安装单个工具

```bash
python tools/go_tools.py install nuclei
python tools/go_tools.py install httpx
python tools/go_tools.py install katana
```

## 📁 项目结构

```
scan/
├── automate_scan.py              # 主扫描脚本
├── simple_scan.py                # 简化版扫描脚本
├── js_analyzer.py               # JavaScript 分析器
├── logger.py                    # 日志工具
├── tools/
│   ├── go_tools.py              # Go 工具管理器 ⭐
│   ├── vuln_report_learner.py   # 漏洞报告学习工具 ⭐
│   ├── hackerone_disclosed.py   # HackerOne 公开报告查询 ⭐
│   └── nikto/                   # 扫描模块
│       ├── url_collector.py     # URL 收集器
│       ├── url_analyzer.py      # URL 分析器
│       ├── scan.py              # Nuclei 扫描器
│       ├── sqlmap_scan.py       # SQLMap 扫描器
│       └── js_analyzer.py       # JS 分析器
├── urls/
│   └── targets.txt              # 目标 URL 列表
├── results/                     # 扫描结果（自动生成）
├── requirements.txt             # Python 依赖
├── README.md                    # 本文件
├── QUICKSTART.md                # 快速开始指南
├── HACKERONE_INTEGRATION.md     # HackerOne 集成说明
└── VULN_REPORT_LEARNING.md      # 漏洞学习指南
```

## 🎯 扫描流程

```
1. HTTP 探测 (httpx)
   ↓
2. URL 收集 (Katana)
   ↓
3. URL 分类分析
   ↓
4. 漏洞扫描 (Nuclei)
   ↓
5. SQL 注入测试 (SQLMap)
   ↓
6. JavaScript 分析
   ↓
7. 生成报告
```

## 📊 输出文件

每个目标的扫描结果保存在 `@域名_bounty/` 目录：

```
@example.com_bounty/
├── all_urls.txt              # 所有收集的 URL
├── valid_urls.txt            # 验证有效的 URL
├── nuclei_scan.txt           # Nuclei 扫描结果
├── sqlmap_targets.txt        # SQLMap 测试目标
├── sqlmap_results.json       # SQLMap 测试结果
├── js_endpoints.txt          # JS 中发现的端点
├── js_secrets.json           # JS 中的敏感信息
├── findings.md               # 漏洞发现汇总
├── progress.md               # 扫描进度记录
└── README.md                 # 扫描总结
```

## 🔐 HackerOne 集成（可选）

如果你想从 HackerOne 自动获取目标或学习公开报告：

### 1. 获取 API Token

1. 登录 HackerOne
2. 访问 https://hackerone.com/settings/api_token
3. 点击 "Generate new token"
4. 复制生成的 Token（只显示一次！）

### 2. 配置到项目

编辑 `.env` 文件（已添加到 `.gitignore`，不会提交）：

```ini
HACKERONE_API_TOKEN=your_token_here
HACKERONE_USERNAME=your_username_here
```

详见：[HACKERONE_SETUP.md](HACKERONE_SETUP.md) - 完整配置指南

### 3. 验证配置

```bash
python tools/hackerone_api.py
```

### 4. 开始扫描

```bash
python automate_scan.py
```

脚本会自动从 HackerOne 获取你的项目目标并开始扫描！

## 💡 使用技巧

### 1. 加速扫描

- 使用 `simple_scan.py` 进行快速扫描
- 调整 Nuclei 并发参数（默认已优化）
- 只扫描关键目标，避免大规模扫描

### 2. 提高准确性

- 确保目标 URL 准确
- 检查 `all_urls.txt` 确认 URL 收集完整
- 手动验证重要漏洞

### 3. 学习最佳实践

- 定期阅读 HackerOne 公开报告
- 分析漏洞模式和利用技巧
- 在合法环境中练习

## ⚠️ 重要提示

1. **合法授权** - 仅扫描你有权测试的目标
2. **遵守法律** - 未经授权的扫描可能违法
3. **负责任披露** - 发现漏洞后负责任地报告
4. **备份数据** - 定期备份重要的扫描结果

## 📖 相关文档

- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南
- [VULN_REPORT_LEARNING.md](VULN_REPORT_LEARNING.md) - 漏洞报告学习指南
- [HACKERONE_INTEGRATION.md](HACKERONE_INTEGRATION.md) - HackerOne 集成说明

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**Happy Hacking! 🔐**

> 记住：始终在授权范围内使用本工具
