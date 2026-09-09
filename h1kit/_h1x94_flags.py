# -*- coding: utf-8 -*-
"""综合提取:featureToggles 全量 + 非 graphql 端点 + graphiql 引用(2026-09-09)"""
import re

with open(r"D:\scan\h1kit\_h1x3_constants.js", "r", encoding="utf-8", errors="replace") as f:
    const_data = f.read()
with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    app_data = f.read()

# A. featureToggles 定义(constants)
print("===== featureToggles(constants)")
for m in re.finditer(r"featureToggles\s*[:=]\s*\{([^}]{0,3000})\}", const_data):
    body = m.group(1)
    for mm in re.finditer(r"([A-Z0-9_]{4,})\s*:\s*[\"'][^\"']*[\"']", body):
        print("  ", mm.group(1))
print("\n===== feature_toggles 字符串(app 里所有 flag 名)")
for m in re.finditer(r"(?:featureToggles|feature_toggles|FT)\.([A-Z][A-Z0-9_]{4,})", app_data):
    print("  ", m.group(1))
