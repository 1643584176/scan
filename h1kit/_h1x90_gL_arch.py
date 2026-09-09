# -*- coding: utf-8 -*-
"""读 gL(mermaid 渲染组件)实现(2026-09-09)"""
with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()
idx = data.find("gL=({id:e,source:t,onSvgContentChange:n,maxHeight:r})=>")
print("idx:", idx)
if idx > 0:
    print(data[idx:idx + 2500])
