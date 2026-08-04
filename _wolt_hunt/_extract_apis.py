# -*- coding: utf-8 -*-
"""全量提取所有 JS chunk 中的 API path，生成端点清单（OpenAPI 风格 + 模板字符串风格）"""
import re, glob, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

paths = collections.Counter()
methods = {}   # path -> set(method)
ctx = {}       # path -> 上下文

method_re = re.compile(r'method:"(GET|POST|PUT|PATCH|DELETE)"')
path_re = re.compile(r'path:"([^"]{2,150})"')
str_re = re.compile(r'"((?:/v1|/v2|/v3|/v4|/cx|/order-xp|/regatta|/wolt)/[a-zA-Z0-9_${}./{}\-]{2,120})"')

for f in sorted(glob.glob("js/*.js")):
    try:
        data = open(f, encoding="utf-8", errors="replace").read()
    except Exception as e:
        print(f"SKIP {f}: {e}")
        continue
    # OpenAPI 风格 path:"..." + method:"..."
    for m in path_re.finditer(data):
        p = m.group(1)
        if not p.startswith(("/v1/", "/v2/", "/v3/", "/v4/", "/cx/", "/order-xp/", "/regatta/")):
            continue
        if "{" in p and "}" not in p:
            continue
        paths[p] += 1
        seg = data[max(0, m.start() - 400):m.start() + 100]
        mm = method_re.search(seg)
        if mm:
            methods.setdefault(p, set()).add(mm.group(1))
        if p not in ctx:
            ctx[p] = data[max(0, m.start() - 200):m.start() + 200]
    # 字符串风格（fetch/axios 模板）
    for m in str_re.finditer(data):
        p = m.group(1)
        if "${" in p or "}" in p:
            continue
        paths[p] += 1
        if p not in ctx:
            ctx[p] = data[max(0, m.start() - 160):m.start() + 160]

print(f"===== 总端点数: {len(paths)} =====")
for p, c in sorted(paths.items(), key=lambda x: -x[1]):
    ms = ",".join(sorted(methods.get(p, []))) or "-"
    print(f"{c:4d} [{ms:12s}] {p}")

# 存详细上下文供后续分析
with open("_api_paths_dump.txt", "w", encoding="utf-8") as fh:
    for p in sorted(paths, key=lambda x: -paths[x]):
        fh.write(f"### {p} (x{paths[p]})\n{ctx[p]}\n\n")
print("\n上下文已存 _api_paths_dump.txt")
