# -*- coding: utf-8 -*-
"""深挖 Mze 调用者 + AI 工具清单(前端)(2026-09-09)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. Mze 调用点:找 "Mze(" 或包含 html2canvas 特征的函数名
# 函数定义前找名字:Mze 变量在 minified 里是 var Mze=(e,t)=>{...}
# 找引用:向后找 "Mze(" 出现点
for m in re.finditer(r"Mze\s*\(", data):
    ctx = data[m.start() - 400:m.start() + 200].replace("\n", " ")
    print(f"CALL>>> {ctx[:600]}")
    print("---")
    if m.start() > 6456593 and m.start() < 7000000:
        break

# 2. AI 工具名(前端硬编码清单?)
for kw in ["docs_citation", "severity_calculation", "report_predicted", "pii_detection", "followup_prompts", "mermaid", "tool_name"]:
    hits = [m.start() for m in re.finditer(re.escape(kw), data)]
    print(f"\n== {kw}: {len(hits)}")
