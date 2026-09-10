# -*- coding: utf-8 -*-
"""写面弹药库:含 report 参数的 mutation 全清单(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 文档串形态:mutation Name($x: ..., $report_id: ...) 或 input 含 report_id
pats = [
    r"mutation\s+([A-Za-z0-9_]+)\s*\(([^)]{0,800}?)\)\s*\{",
]
seen = {}
for p in pats:
    for m in re.finditer(p, data):
        name, args = m.groups()
        if re.search(r"report|Report", args) and name not in seen:
            seen[name] = args[:300]

print(f"== 含 report 参数的 mutation: {len(seen)}")
for name, args in sorted(seen.items()):
    # 提取变量名
    vars_ = re.findall(r"\$([A-Za-z0-9_]+)", args)
    print(f"  {name}: {vars_}")
