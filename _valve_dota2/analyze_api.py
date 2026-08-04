# -*- coding: utf-8 -*-
"""dota2 JS 静态分析:提取 TS 配置、URL 字面量、API 调用"""
import re, os, json
from collections import Counter

JS = r"D:/scan/_valve_dota2/js"
out = {}

# 1. 找 TS 配置对象定义(Nr.TS = {...})
for fname in ["main.js", "libraries.js"]:
    src = open(os.path.join(JS, fname), encoding="utf-8", errors="replace").read()
    # 模式: {..., TS: {...}} 或 TS = {...} 或 TS:{...}
    for m in re.finditer(r"(?:[A-Za-z_$][\w$]*\.)?TS\s*[:=]\s*\{", src):
        start = m.start()
        # 平衡括号取对象体
        depth = 0
        i = src.index("{", m.start())
        j = i
        while j < len(src):
            if src[j] == "{": depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        body = src[i:j+1]
        if "BASE_URL" in body:
            print(f"=== TS 配置定义 @{start} in {fname} ===")
            print(body[:1500])
            print()
            break

# 2. 全部 URL 字面量(https://)
urls = Counter()
for fname in os.listdir(JS):
    if not fname.endswith(".js"): continue
    src = open(os.path.join(JS, fname), encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'["\'](https?://[^"\']{8,150})["\']', src):
        u = m.group(1)
        # 去掉模板变量
        if "${" in u: continue
        urls[u] += 1

print("=== URL 字面量 top 60 ===")
for u, c in urls.most_common(60):
    print(f"{c:4d}  {u}")

# 3. axios 风格 .get/.post 调用 URL(相对路径字面量)
print("\n=== .get/.post 相对路径调用 ===")
calls = Counter()
for fname in ["main.js"]:
    src = open(os.path.join(JS, fname), encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'\.(get|post|put|delete)\(\s*["\'](/[^"\']{3,120})["\']', src):
        calls[m.group(2)] += 1
for u, c in calls.most_common(40):
    print(f"{c:4d}  {u}")
