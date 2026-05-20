# 安全扫描工具命令清单

本文档记录了项目中所有使用的外部工具命令及其参数说明。

---

## 1. Katana (URL 爬虫)

### 命令位置
`tools/nikto/katana_all_url.py` - `run_katana()` 函数

### 完整命令
```bash
katana -u <target_url> -d 3 -c 10 -timeout 5 -f url -known-files all -silent
```

### 参数说明
| 参数 | 值 | 说明 |
|------|-----|------|
| `-u` | `<target_url>` | 目标 URL |
| `-d` | `3` | 爬取深度（3=首页+一级+二级链接） |
| `-c` | `10` | 并发数（10个线程） |
| `-timeout` | `5` | 单个请求超时（5秒） |
| `-f` | `url` | 只输出 URL |
| `-known-files` | `all` | 爬取 robots.txt、sitemap.xml |
| `-silent` | - | 静默模式，减少输出 |

### Python 调用
```python
subprocess.run(
    cmd,
    stdout=outfile,
    stderr=subprocess.STDOUT,
    timeout=60  # Python 层面总超时 60 秒
)
```

### 输出文件
- `katana_raw.txt` - 原始爬取的 URL 列表

---

## 2. httpx (URL 验证)

### 命令位置
`tools/nikto/katana_all_url.py` - `run_httpx()` 函数

### 完整命令
```bash
httpx -l <input_file> -o <output_file> -mc 200,201,204,301,302,307,403 -silent -timeout 8 -retries 0 -t 50
```

### 参数说明
| 参数 | 值 | 说明 |
|------|-----|------|
| `-l` | `<input_file>` | 输入文件（URL 列表） |
| `-o` | `<output_file>` | 输出文件（有效 URL） |
| `-mc` | `200,201,204,301,302,307,403` | 只保留这些状态码 |
| `-silent` | - | 静默模式 |
| `-timeout` | `8` | 单个请求超时（8秒） |
| `-retries` | `0` | 不重试 |
| `-t` | `50` | 并发线程数（50个） |

### Python 调用
```python
subprocess.run(cmd, capture_output=True)
# 注意：不设置 timeout，让 httpx 自然完成
```

### 输入/输出文件
- 输入：`temp_urls.txt` - 待验证的 URL 列表
- 输出：`httpx_valid.txt` - 验证后的有效 URL

---

## 3. Nuclei (漏洞扫描)

### 命令位置
`tools/nikto/scan.py`

### 三种扫描模式

#### 模式1: 快速扫描（5-10分钟）
```bash
python scan.py <target_url> [output_dir] fast
```
**配置：**
- 严重级别：critical, high
- 并发数：25
- 速率限制：150 req/s
- 排除标签：fuzz, headless, network, dns, ssl, file, osint, mobile, app, android, ios, info, low, medium

#### 模式2: 标准扫描（10-15分钟）✅ 推荐
```bash
python scan.py <target_url> [output_dir] standard
```
**配置：**
- 严重级别：critical, high, medium
- 并发数：25
- 速率限制：150 req/s
- 排除标签：fuzz, headless, network, dns, ssl, file, osint, mobile, app, android, ios, info, low

#### 模式3: 全面扫描（15-25分钟）
```bash
python scan.py <target_url> [output_dir] full
```
**配置：**
- 严重级别：critical, high, medium, low
- 并发数：20
- 速率限制：100 req/s
- 排除标签：fuzz, headless, network, dns, ssl, file, osint, mobile, app, android, ios, info

### 参数说明
| 参数 | 值 | 说明 |
|------|-----|------|
| `-u` | `<target_url>` | 目标 URL |
| `-o` | `<output_file>` | 输出文件 |
| `-c` | `10` | 并发数 |
| `-timeout` | `30` | 请求超时（30秒） |
| `-rate-limit` | `50` | 速率限制（50请求/秒） |
| `-retries` | `0` | 不重试 |
| `-severity` | `critical,high,medium,low` | 漏洞严重程度 |
| `-exclude-tags` | `fuzz,headless,...` | 排除的标签 |
| `-stats` | - | 显示统计信息 |

### 更新命令
```bash
# 检查并更新模板
nuclei -update-templates -silent

# 更新引擎
nuclei -update
```

### 输出文件
- `nuclei_scan.txt` - 漏洞扫描结果

---

## 4. SQLMap (SQL 注入测试)

### 命令位置
`tools/nikto/sqlmap_scan.py`

### 完整命令（快速模式）
```bash
sqlmap -u "<target_url>" --batch --level 1 --risk 1 --timeout 10 --threads 5 --random-agent --technique BEUSTQ -v 0 --answers "follow=N" --skip-waf --no-cast --flush-session
```

### 参数说明
| 参数 | 值 | 说明 |
|------|-----|------|
| `-u` | `"<target_url>"` | 目标 URL（带参数） |
| `--batch` | - | 自动选择默认选项 |
| `--level` | `1` | 测试级别（1=最快） |
| `--risk` | `1` | 风险等级（1=最低） |
| `--timeout` | `10` | 请求超时（10秒） |
| `--threads` | `5` | 线程数 |
| `--random-agent` | - | 随机 User-Agent |
| `--technique` | `BEUSTQ` | 测试技术 |
| `-v` | `0` |  verbosity（0=最少输出） |
| `--answers` | `"follow=N"` | 自动回答 |
| `--skip-waf` | - | 跳过 WAF 检测 |
| `--no-cast` | - | 不使用类型转换 |
| `--flush-session` | - | 清除会话 |

### 输出文件
- `sqlmap_results.json` - 测试结果

---

## 5. 其他工具

### 5.1 Go 工具安装/更新
```bash
# 安装/更新 Katana
go install github.com/projectdiscovery/katana/cmd/katana@latest

# 安装/更新 httpx
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
```

### 5.2 Python 包更新
```bash
# 更新 SQLMap
pip install --upgrade sqlmap
```

---

## 命令执行流程

```
1. URL 收集阶段
   ├─ Katana 爬取 → katana_raw.txt
   ├─ 过滤 URL → filtered_urls
   └─ httpx 验证 → httpx_valid.txt → all_urls.txt

2. URL 分类阶段
   └─ url_analyzer.py → url_classification.json, sqlmap_targets.txt

3. 漏洞扫描阶段
   ├─ Nuclei 扫描 → nuclei_scan.txt
   └─ SQLMap 测试 → sqlmap_results.json

4. JS 分析阶段
   └─ js_analyzer.py → js_endpoints.txt, js_secrets.json

5. 报告生成
   └─ generator.py → findings.md, progress.md, README.md
```

---

## 超时配置汇总

| 工具 | 单请求超时 | 总超时 | 并发数 |
|------|-----------|--------|--------|
| **Katana** | 5 秒 | 60 秒 (Python) | 10 |
| **httpx** | 8 秒 | 无限制 | 50 |
| **Nuclei** | 30 秒 | 900 秒 (15分钟) | 10 |
| **SQLMap** | 10 秒 | 1200 秒 (20分钟) | 5 |

---

## 常见问题

### Q1: httpx 验证很慢？
**A**: 检查以下几点：
- URL 数量是否过多（>1000）
- 网络连接是否正常
- 目标网站是否有防护（WAF/CDN）
- 尝试降低并发数（`-t 20`）

### Q2: Katana 爬取超时？
**A**: 
- 增加 `-ct` 参数（如果支持）
- 降低并发数（`-c 5`）
- 使用降级方案（robots.txt + sitemap）

### Q3: Nuclei 扫描太慢？
**A**:
- 减少 `-c` 并发数
- 增加 `-rate-limit`
- 使用 `-tags` 限定扫描范围

---

*最后更新: 2026-05-20*
