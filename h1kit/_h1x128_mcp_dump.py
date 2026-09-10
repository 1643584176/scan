# -*- coding: utf-8 -*-
"""MCP SDK 全貌提取:sandbox 消息处理/CSP/权限/readResource 链(2026-09-09)"""
import re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

text = open(r"D:\scan\h1kit\_h1x4_vendor.js", encoding="utf-8", errors="replace").read()

# 1. mcp-app 定位并前向展开大段
i = text.find("mRr=`text/html;profile=mcp-app`")
print("mcp-app idx:", i, flush=True)
seg = text[i:i + 40000]
open(r"D:\scan\h1kit\_h1x128_mcp_seg.txt", "w", encoding="utf-8").write(seg)
print("saved seg len:", len(seg), flush=True)

# 2. sandbox-resource-ready 处理(收消息方)另找
j = text.find("sandbox-resource-ready")
print("sbr idx:", j, flush=True)
j2 = text.find("sandbox-resource-ready", j + 30)
print("sbr2 idx:", j2, flush=True)
if j2 > 0:
    seg2 = text[j2 - 20000:j2 + 10000]
    open(r"D:\scan\h1kit\_h1x129_sbr_seg.txt", "w", encoding="utf-8").write(seg2)
    print("saved seg2 len:", len(seg2), flush=True)
