# -*- coding: utf-8 -*-
"""从全部 JS 批量提取 API 路径，生成接口清单（按域分组、去重、统计）"""
import re, sys, glob, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIRS = ["js", "merchant_js", "ops_js"]
FILES = []
for d in SRC_DIRS:
    FILES += glob.glob(os.path.join(ROOT, d, "*.js"))
FILES += [os.path.join(ROOT, "corporate_main.js")]  # 15MB 企业端

# 提取所有形如 /vN/xxx 的路径字面量（含模板 ${}）
path_re = re.compile(r'["\'`](/[A-Za-z0-9_\-\./{}${}]*?)["\'`]')
# 也提取拼出来的: concat("...","...") 及 /api/ 前缀
paths = {}
for f in FILES:
    if not os.path.exists(f):
        continue
    data = open(f, encoding="utf-8", errors="replace").read()
    for m in path_re.finditer(data):
        p = m.group(1)
        if not (p.startswith("/v") or p.startswith("/api") or p.startswith("/order-xp") or p.startswith("/graphql")):
            continue
        # 规范化：去掉 ${...} 与查询串，只留结构
        seg = re.sub(r"\$\{[^}]*\}", "{id}", p)
        seg = seg.split("?")[0]
        if len(seg) < 3 or len(seg) > 120:
            continue
        # 忽略纯静态资源
        if re.search(r"\.(js|css|png|svg|ico|json|map|html)$", seg):
            continue
        paths.setdefault(seg, 0)
        paths[seg] += 1

# 按接口族分组排序
families = {}
for p, c in sorted(paths.items(), key=lambda x: -x[1]):
    # 取第一段作为族
    parts = [x for x in p.split("/") if x]
    family = "/" + parts[0] if parts else p
    if len(parts) > 1:
        family = "/" + parts[0] + "/" + parts[1]
    families.setdefault(family, []).append((p, c))

print(f"TOTAL unique paths: {len(paths)}")
print("=" * 70)
for fam, items in sorted(families.items(), key=lambda x: -len(x[1])):
    print(f"\n### {fam}  ({len(items)} endpoints)")
    for p, c in items[:12]:
        print(f"   {c:>3}  {p}")
    if len(items) > 12:
        print(f"   ... +{len(items)-12} more")
