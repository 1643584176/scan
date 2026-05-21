# Subfinder 子域名扫描集成说明

## 📋 概述

项目已集成 Subfinder 子域名扫描功能，在扫描主域名之前会自动发现并扫描所有子域名。

## 🚀 功能特点

### 1. 自动化子域名发现
- 在扫描流程最开始执行（步骤0/7）
- 使用 ProjectDiscovery 的 Subfinder 工具
- 自动移除不活跃的子域名
- 最大运行时间 5 分钟

### 2. 完全解耦设计
- 独立模块：`modules/subdomain_scan.py`
- 可单独运行：`python modules/subdomain_scan.py example.com ./output`
- 不影响现有扫描流程

### 3. 智能扫描策略
```
主域名扫描
  ↓
发现子域名 (例如: api.example.com, admin.example.com)
  ↓
对每个子域名独立执行完整扫描流程
  - 技术栈检测
  - URL 收集
  - 漏洞扫描
  - JS 分析
  - SQLMap 测试
  - 生成报告
```

## 📦 安装 Subfinder

### 方法1：使用 Go 安装（推荐）
```bash
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

### 方法2：使用项目工具管理器
```bash
python tools/go_tools.py install subfinder
```

### 验证安装
```bash
subfinder -version
```

## 🔧 使用方法

### 自动扫描（推荐）
```bash
# 正常运行，会自动包含子域名扫描
python main.py
```

**扫描流程：**
```
[步骤0/7] 子域名扫描
  → 发现 15 个子域名
  
[子域名 1/15] 扫描: https://api.example.com
  [步骤1/6] HTTP 探测
  [步骤2/6] URL 收集
  ...
  
[子域名 2/15] 扫描: https://admin.example.com
  ...
  
[主域名] 扫描: https://example.com
  ...
```

### 单独运行子域名扫描
```bash
# 仅扫描子域名，不执行后续步骤
python modules/subdomain_scan.py example.com ./output_dir
```

**输出文件：**
- `subdomains.txt` - 发现的子域名列表
- `subdomain_stats.json` - 统计信息

## 📊 输出示例

### subdomains.txt
```
api.example.com
admin.example.com
dev.example.com
staging.example.com
mail.example.com
```

### subdomain_stats.json
```json
{
  "domain": "example.com",
  "total_subdomains": 15,
  "subdomains": [
    "api.example.com",
    "admin.example.com",
    ...
  ]
}
```

## 💡 实际应用场景

### 场景1：发现隐藏的管理后台
```
主域名: example.com
  → 未发现管理入口

子域名扫描发现:
  - admin.example.com  ← 管理后台！
  - dashboard.example.com  ← 仪表盘！
  
对这些子域名进行深度扫描，可能发现：
  - 默认凭证
  - 未授权的访问
  - 配置错误
```

### 场景2：API 端点发现
```
子域名扫描发现:
  - api.example.com
  - api-v2.example.com
  - graphql.example.com
  
重点测试：
  - IDOR 漏洞
  - 认证绕过
  - 速率限制
  - 注入漏洞
```

### 场景3：开发/测试环境泄露
```
子域名扫描发现:
  - dev.example.com
  - staging.example.com
  - test.example.com
  
这些环境通常：
  - 安全性较弱
  - 有调试信息泄露
  - 使用默认配置
  - 更容易发现漏洞
```

## ⚙️ 配置选项

### 环境变量
当前子域名扫描使用默认配置，未来可以添加：

```bash
# .env 文件（待添加）
SUBDOMAIN_MAX_TIME=300      # 最大扫描时间（秒）
SUBDOMAIN_REMOVE_INACTIVE=true  # 移除不活跃子域名
SKIP_SUBDOMAIN_SCAN=false   # 跳过子域名扫描
```

### 修改扫描参数
编辑 `modules/subdomain_scan.py`：

```python
cmd = [
    subfinder_exe,
    '-d', domain,
    '-o', output_file,
    '-silent',
    '-nW',              # 移除不活跃的域名
    '-max-time', '300'  # 改为 600 增加扫描时间
]
```

## 🔍 故障排除

### 问题1：未找到 subfinder 命令

**错误信息：**
```
[✗] 未找到 subfinder 命令
安装方法: go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

**解决方案：**
```bash
# 安装 Subfinder
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# 验证安装
which subfinder  # Linux/Mac
where subfinder  # Windows
```

### 问题2：子域名扫描超时

**原因：** 
- 目标域名有很多子域名
- 网络速度慢
- DNS 查询超时

**解决方案：**
```python
# 编辑 modules/subdomain_scan.py
# 增加超时时间
timeout=900  # 从 600 改为 900（15分钟）

# 或减少 max-time
'-max-time', '600'  # 从 300 改为 600（10分钟）
```

### 问题3：发现的子域名太少

**原因：**
- Subfinder 默认数据源有限
- 目标使用了私有子域名

**解决方案：**
```python
# 编辑 modules/subdomain_scan.py
# 添加更多数据源（需要配置 API Key）
cmd = [
    subfinder_exe,
    '-d', domain,
    '-o', output_file,
    '-silent',
    '-nW',
    '-max-time', '300',
    '-recursive',     # 启用递归搜索
    '-all'            # 使用所有数据源
]
```

**配置 API Keys（可选）：**
创建 `~/.config/subfinder/provider-config.yaml`：
```yaml
virustotal: YOUR_API_KEY
shodan: YOUR_API_KEY
censys: YOUR_API_KEY
```

## 📈 性能优化建议

### 1. 并行扫描子域名
当前实现是串行扫描每个子域名，未来可以优化：

```python
# 伪代码
with ThreadPoolExecutor(max_workers=3) as executor:
    for subdomain in subdomains:
        executor.submit(scan_single_subdomain, subdomain)
```

### 2. 优先级排序
```python
# 优先扫描高价值子域名
priority_keywords = ['api', 'admin', 'dev', 'staging']
priority_subs = [s for s in subdomains if any(k in s for k in priority_keywords)]
regular_subs = [s for s in subdomains if s not in priority_subs]

# 先扫描优先级高的
for sub in priority_subs:
    scan(sub)
```

### 3. 缓存结果
```python
# 如果 subdomains.txt 已存在且小于24小时，直接使用
if os.path.exists('subdomains.txt'):
    if file_age < 24 hours:
        use_cached_results()
```

## 🎯 HackerOne 挖洞技巧

### 技巧1：关注非常规子域名
```
常见但容易被忽略的子域名：
- internal.example.com
- vpn.example.com
- jira.example.com
- gitlab.example.com
- confluence.example.com
- monitoring.example.com
```

### 技巧2：检查子域名枚举差异
```
运行多次扫描，对比结果：
第一次: 15 个子域名
第二次: 18 个子域名  ← 新增的 3 个值得重点关注！
```

### 技巧3：结合其他工具
```bash
# 1. Subfinder 发现子域名
python modules/subdomain_scan.py example.com ./output

# 2. 使用 httpx 验证存活
httpx -l subdomains.txt -o active_subdomains.txt

# 3. 对存活的子域名进行深度扫描
python main.py  # 会自动处理
```

### 技巧4：监控新子域名
```bash
# 定期运行子域名扫描
# 对比历史结果，发现新增子域名
diff old_subdomains.txt new_subdomains.txt
```

## 🔒 安全注意事项

### 1. 授权范围确认
```
确保子域名也在授权范围内：
✓ *.example.com (通配符授权)
✗ third-party.example.com (第三方服务，可能未授权)
```

### 2. 速率控制
```
子域名扫描会产生大量请求：
- Subfinder: DNS 查询
- 后续扫描: HTTP 请求

建议：
- 设置 SCAN_WORKERS=1（单线程）
- 避免同时对多个主域名扫描
```

### 3. 尊重目标
```
- 不要频繁扫描同一目标
- 发现严重漏洞立即报告
- 避免对生产环境造成压力
```

## 📚 相关文档

- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - 性能优化说明
- [SECURITY_AND_INTELLIGENCE_OPTIMIZATION.md](SECURITY_AND_INTELLIGENCE_OPTIMIZATION.md) - 安全与智能优化
- [Subfinder 官方文档](https://github.com/projectdiscovery/subfinder)

---

*最后更新: 2026-05-20*
