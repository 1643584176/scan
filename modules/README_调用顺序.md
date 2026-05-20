# 模块调用顺序说明

## 📊 完整执行流程

```
启动 main.py
    │
    ├─→ 1. 初始化
    │     ├─ setup_encoding()      # 设置 UTF-8 编码
    │     ├─ load_env_file()       # 加载 .env 配置
    │     └─ update_all()          # 更新所有工具（并行）
    │           ├─ update_nuclei()
    │           ├─ update_katana()
    │           ├─ update_httpx()
    │           └─ update_sqlmap()
    │
    ├─→ 2. 读取 URLs
    │     └─ 从 urls/*.txt 读取目标 URL 列表
    │
    └─→ 3. 对每个 URL 执行 scan_single_url()
          │
          ├─→ 步骤 1/6: 技术栈检测
          │     └─ modules/tech_detect.py
          │         └─ detect_tech_stack(url, bounty_dir)
          │             └─ 调用 httpx -tech-detect
          │
          ├─→ 步骤 2/6: URL 收集
          │     └─ modules/url_collector_module.py
          │         └─ collect_urls(url, bounty_dir)
          │             └─ 调用 tools/nikto/url_collector.py
          │             └─ 输出: all_urls.txt
          │
          ├─→ 步骤 3/6: URL 分类分析
          │     └─ modules/url_analyzer_module.py
          │         └─ analyze_urls(all_urls_file, bounty_dir)
          │             └─ 调用 tools/nikto/url_analyzer.py
          │             └─ 输出: url_classification.json
          │
          ├─→ 步骤 4/6: Nuclei 漏洞扫描
          │     └─ modules/vuln_scanner.py
          │         └─ scan_vulnerabilities(url, bounty_dir)
          │             └─ 调用 tools/nikto/scan.py
          │             └─ 输出: nuclei_scan.txt
          │
          ├─→ 步骤 5/6: JavaScript 文件分析
          │     └─ modules/js_analyzer_module.py
          │         └─ analyze_js_files(all_urls_file, bounty_dir)
          │             └─ 调用 tools/nikto/js_analyzer.py
          │             └─ 输出: js_endpoints.txt, js_secrets.json
          │
          ├─→ 步骤 6/6: SQLMap 注入测试（条件执行）
          │     └─ 检查 sqlmap_targets.txt 是否存在
          │     └─ modules/sqlmap_test.py
          │         └─ test_sql_injection(sqlmap_targets_file, bounty_dir)
          │             └─ 调用 tools/nikto/sqlmap_scan.py
          │             └─ 输出: sqlmap_results.json
          │
          └─→ 最后: 生成报告
                └─ report/generator.py
                    └─ generate_report(bounty_dir, url, tech_stack, all_urls)
                        ├─ 读取 nuclei_scan.txt
                        ├─ 读取 sqlmap_results.json
                        ├─ 生成 findings.md
                        ├─ 更新 progress.md
                        └─ 更新 README.md
```

## 🔢 模块调用顺序总结

| 步骤 | 模块文件 | 功能 | 输入 | 输出 |
|------|---------|------|------|------|
| 0 | tools/updater.py | 工具更新 | - | 更新 Nuclei/Katana/httpx/SQLMap |
| 1 | modules/tech_detect.py | 技术栈检测 | URL | tech_stack.json |
| 2 | modules/url_collector.py | URL 收集 | URL | all_urls.txt |
| 3 | modules/url_analyzer.py | URL 分类 | all_urls.txt | url_classification.json |
| 4 | modules/vuln_scanner.py | 漏洞扫描 | URL | nuclei_scan.txt |
| 5 | modules/js_analyzer.py | JS 分析 | all_urls.txt | js_endpoints.txt, js_secrets.json |
| 6 | modules/sqlmap_test.py | SQL 注入测试 | sqlmap_targets.txt | sqlmap_results.json |
| 7 | report/generator.py | 报告生成 | 所有结果文件 | findings.md, progress.md, README.md |

## 🎯 关键依赖关系

```
步骤 2 (URL 收集) 
    ↓ 生成 all_urls.txt
步骤 3 (URL 分类) ← 需要 all_urls.txt
    ↓
步骤 5 (JS 分析) ← 需要 all_urls.txt
    ↓ 生成 sqlmap_targets.txt
步骤 6 (SQLMap 测试) ← 需要 sqlmap_targets.txt（可选）
    ↓
步骤 7 (报告生成) ← 需要所有结果文件
```

## 💡 单独运行示例

```bash
# 只运行技术栈检测
python modules/tech_detect.py https://example.com ./output

# 只运行 URL 收集
python modules/url_collector.py https://example.com ./output

# 只运行 URL 分类（需要先有 all_urls.txt）
python modules/url_analyzer.py ./output/all_urls.txt ./output

# 只运行漏洞扫描
python modules/vuln_scanner.py https://example.com ./output

# 只运行 JS 分析（需要先有 all_urls.txt）
python modules/js_analyzer.py ./output/all_urls.txt ./output

# 只运行 SQLMap 测试（需要先有 sqlmap_targets.txt）
python modules/sqlmap_test.py ./output/sqlmap_targets.txt ./output

# 只生成报告
python report/generator.py ./output https://example.com

# 只更新工具
python tools/updater.py
```

## ⚠️ 注意事项

1. **步骤 2 必须先于步骤 3、5** - 因为需要 `all_urls.txt`
2. **步骤 6 是可选的** - 只有存在 `sqlmap_targets.txt` 时才执行
3. **步骤 7 应该最后执行** - 需要收集所有结果文件
4. **每个模块都可以独立运行** - 方便调试和测试单个功能
