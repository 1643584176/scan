# -*- coding: utf-8 -*-
"""找 API Token 设置页路由 + 查 has_api_token(2026-09-09)"""
import re

fn = r"D:\scan\h1kit\_src_chunks\user_settings_router-DKsq46eC.js"
with open(fn, "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 路由表:找所有 path 定义(用户设置页)
for m in re.finditer(r"path\s*:\s*[\"']([^\"']+)[\"']", data):
    p = m.group(1)
    if "settings" in p or "api" in p.lower() or "token" in p.lower():
        print("ROUTE:", p)
print("---")
# 组件映射(title:"API Token" 的组件——找 cs 或类似变量的路由绑定)
# 找 "API Token" title 组件
for m in re.finditer(r"title:\s*`API Token`", data):
    ctx = data[max(0, m.start() - 3000):m.start()]
    # 在该组件定义范围内找 route path(往前找最近 route 定义)
    print("CTX HEAD>>>", ctx[-800:].replace("\n", " "))
    print("===")
    break
