# -*- coding: utf-8 -*-
"""源码审计 pass4:提取所有网络调用端点(ajax/fetch/axios/URL 拼接)(2026-09-09)"""
import os, re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\scan\h1kit\_src_chunks"
EXTRA = [r"D:\scan\h1kit\_h1x3_constants.js", r"D:\scan\h1kit\_h1x4_app.js"]

files = [os.path.join(SRC, f) for f in os.listdir(SRC) if f.endswith(".js")] + EXTRA

# 各类网络调用模式
PATS = [
    (r'\.ajax\(\s*\{[^}]{0,200}?url:\s*[`"\']([^`"\']+)', "AJAX"),
    (r'\.ajax\(\s*[`"\']([^`"\']+)', "AJAX2"),
    (r'fetch\(\s*[`"\']([^`"\']+)', "FETCH"),
    (r'axios\.(?:get|post|put|delete|patch)\s*\(\s*[`"\']([^`"\']+)', "AXIOS"),
    (r'url:\s*[`"\'](/(?:api|internal|staff|admin|v[0-9]|graphql)[^`"\']*)', "URLP"),
]

def ctx(text, m, half=120):
    s = max(0, m.start() - half)
    e = min(len(text), m.end() + half)
    return text[s:e].replace("\n", " ")

seen = set()
out_lines = []
for f in files:
    try:
        text = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    name = os.path.basename(f)
    if name.startswith("vendor"):
        continue
    for pat, tag in PATS:
        for m in re.finditer(pat, text):
            u = m.group(1)
            if u in seen:
                continue
            seen.add(u)
            out_lines.append(f"[{tag}] {name}\n  {u}\n  {ctx(text, m)}\n")

res = "\n".join(out_lines)
open(r"D:\scan\h1kit\_h1x124_endpoints.txt", "w", encoding="utf-8").write(res)
print(f"unique endpoints: {len(seen)}")
print(res[:5000])
