# -*- coding: utf-8 -*-
"""graphiql 引用考古 + 非 graphql 端点提取(2026-09-09)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

print("===== graphiql 引用")
for m in re.finditer(r"graphiql", data):
    ctx = data[max(0, m.start() - 300):m.start() + 300].replace("\n", " ")
    print(f">>> {ctx[:550]}")
    print("---")
