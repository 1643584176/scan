# -*- coding: utf-8 -*-
"""定位 API Token 页面组件(用户看到的文案),提取完整实现"""
import os
import re

roots = [r"D:\scan\h1kit\_src_chunks", r"D:\scan\h1kit"]
needle = "You have an active API token"
hits = []
for root in roots:
    if not os.path.isdir(root):
        continue
    for fn in os.listdir(root):
        if not fn.endswith(".js"):
            continue
        p = os.path.join(root, fn)
        try:
            data = open(p, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for m in re.finditer(re.escape(needle), data):
            hits.append((p, m.start()))
for p, pos in hits:
    print("FILE:", p, "pos:", pos)
    data = open(p, "r", encoding="utf-8", errors="replace").read()
    # 提取该组件函数(往前找 function 边界太复杂;取前后 6000 字符)
    seg = data[max(0, pos - 6000):pos + 6000]
    open(r"D:\scan\h1kit\_h1x136_token_page_seg.txt", "w", encoding="utf-8").write(seg)
    print("saved seg len", len(seg))
    break
if not hits:
    print("no hits in chunks; try app.js")
    data = open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace").read()
    for m in re.finditer(re.escape(needle), data):
        print("APP.JS pos:", m.start())
