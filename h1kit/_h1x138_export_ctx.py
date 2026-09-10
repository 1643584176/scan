# -*- coding: utf-8 -*-
"""提取 export/raw + export/zip 组件完整实现上下文"""
import re

data = open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace").read()

for needle in ["/export/raw", "/export/zip"]:
    idx = data.find(needle)
    print("==== needle:", needle, "pos:", idx)
    if idx > 0:
        seg = data[max(0, idx - 4000):idx + 2500]
        open(r"D:\scan\h1kit\_h1x138_export_seg.txt", "w", encoding="utf-8").write(seg)
        print("saved", len(seg))
