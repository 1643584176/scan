# -*- coding: utf-8 -*-
"""提取 cG(AgenticUiMcp renderer)完整实现 + sandbox iframe 搭建(2026-09-09)"""
import io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

text = open(r"D:\scan\h1kit\_h1x4_app.js", encoding="utf-8", errors="replace").read()

# 定位 cG 定义段:从 zGe 协议白名单开始往后 6000 字符
i = text.find("var zGe=[`http:`")
print("zGe idx:", i)
seg = text[i:i + 9000]
open(r"D:\scan\h1kit\_h1x126_cg_seg.txt", "w", encoding="utf-8").write(seg)
print(seg[:9000])
