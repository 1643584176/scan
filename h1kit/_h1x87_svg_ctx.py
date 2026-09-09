# -*- coding: utf-8 -*-
"""深挖 app 里唯一的 innerHTML=(SVG 处理)(2026-09-09)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 找 innerHTML= 的完整上下文(前后 3000 字符)
for m in re.finditer(r"\.innerHTML\s*=", data):
    start = max(0, m.start() - 3000)
    ctx = data[start:m.start() + 500]
    print(f"===== hit at {m.start()}")
    print(ctx[-2500:])
    print("\n\n")
