# -*- coding: utf-8 -*-
"""找 API Token modal 入口(所在设置页/菜单)(2026-09-09)"""
import re

fn = r"D:\scan\h1kit\_src_chunks\user_settings_router-DKsq46eC.js"
with open(fn, "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# Generate API Token 文案前后
for kw in ["Generate API Token", "legacyTitle", "has_api_token", "API token"]:
    for m in re.finditer(re.escape(kw), data, re.I):
        ctx = data[max(0, m.start() - 800):m.start() + 400].replace("\n", " ")
        print(f"[{kw}] >>> {ctx[:900]}")
        print("---")
        break
