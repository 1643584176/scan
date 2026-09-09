# -*- coding: utf-8 -*-
"""找 ob hook(renderDiagram)实现 + mermaid 版本(2026-09-09)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# ob() 引用上下文
for m in re.finditer(r"\bob\s*=\s*\(", data):
    ctx = data[max(0, m.start() - 300):m.start() + 400].replace("\n", " ")
    print(f">>> {ctx[:600]}")
    print("---")
# 找 renderDiagram 定义
for m in re.finditer(r"renderDiagram", data):
    ctx = data[max(0, m.start() - 200):m.start() + 300].replace("\n", " ")
    print(f"RD>>> {ctx[:450]}")
    print("---")
    break
