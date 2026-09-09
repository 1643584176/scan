# -*- coding: utf-8 -*-
"""源码资产盘点:主 bundle 大小 + chunk 清单全量提取(2026-09-09)"""
import os
import re

paths = {
    "app": r"D:\scan\h1kit\_h1x4_app.js",
    "main": r"D:\scan\h1kit\_h1x3_main.js",
    "constants": r"D:\scan\h1kit\_h1x3_constants.js",
    "vendor": r"D:\scan\h1kit\_h1x4_vendor.js",
}
for k, p in paths.items():
    if os.path.exists(p):
        print(f"{k}: {os.path.getsize(p)/1024/1024:.1f} MB")

# chunk 清单:从主 bundle 提取所有 static/xxx.js 引用
chunks = set()
with open(paths["app"], "r", encoding="utf-8", errors="replace") as f:
    data = f.read()
for m in re.finditer(r"static/([a-z_0-9]+-[A-Za-z0-9_-]+\.js)", data):
    chunks.add(m.group(1))
print(f"\napp bundle 引用的 chunk 数: {len(chunks)}")

# 分类统计(按前缀)
from collections import Counter
pref = Counter(c.split("-")[0] for c in chunks)
print("\nTop 前缀:")
for p_, n in pref.most_common(40):
    print(f"  {p_}: {n}")
