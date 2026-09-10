# -*- coding: utf-8 -*-
"""读 _L(chart artifact)完整实现(2026-09-09)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 定位 _L 定义(mermaid 渲染代码之后)
idx = data.find("_L=({artifact:e})=>")
if idx < 0:
    idx = data.find("_L = ({artifact:e}) =>")
print("idx:", idx)
if idx > 0:
    print(data[idx - 200:idx + 2500])
