# -*- coding: utf-8 -*-
"""考古:intent 读查询形态(Query 根字段)(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. Query 根含 intent 的查询文档串
for m in re.finditer(r"(query|fragment)\s+[A-Za-z0-9_]*Intent[A-Za-z0-9_]*", data):
    start = data.rfind('"', 0, m.start())
    seg = data[start:m.start() + 600].replace("\\n", "\n")
    if re.search(r"(query|fragment)", seg[:100]):
        print(seg[:550])
        print("---")
        if m.start() > 0 and seg.count("---") > 3:
            break
