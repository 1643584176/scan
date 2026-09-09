# -*- coding: utf-8 -*-
"""找 API Token 设置页路由路径(2026-09-09)"""
import re

fn = r"D:\scan\h1kit\_src_chunks\user_settings_router-DKsq46eC.js"
with open(fn, "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 找 API Token 页组件 + 路由 path
for m in re.finditer(r"API Token", data):
    ctx = data[max(0, m.start() - 1500):m.start() + 200]
    # 往回找 path:
    idx = ctx.rfind("path:")
    if idx >= 0:
        print("PATH>>>", ctx[idx:idx + 200])
    # 找组件名和 Route
    print("CTX>>>", data[m.start() - 200:m.start() + 100].replace("\n", " "))
    print("---")
    break

# 找所有 route path 定义(settings 路由表)
for m in re.finditer(r"path\s*:\s*[\"'](/settings[^\"']*)[\"']", data):
    print("ROUTE:", m.group(1))
