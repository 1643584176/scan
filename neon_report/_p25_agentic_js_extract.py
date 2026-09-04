# -*- coding: utf-8 -*-
"""JS bundle 全量提取 agentic_provisioning 相关端点字符串(找发起端/其他子路径)"""
import re, os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_js', 'app.js')
src = open(p, encoding='utf-8', errors='replace').read()
print('app.js size:', len(src), flush=True)

# 1. 所有出现位置
idxs = [m.start() for m in re.finditer(r'agentic[_A-Za-z]*[Pp]rovisioning|agentic_provisioning|AgenticProvisioning', src)]
print('occurrences:', len(idxs), flush=True)

# 2. 提取每个出现位置前后 400 字符的字符串字面量(端点 URL 形态)
pats = []
for i in idxs:
    seg = src[max(0, i - 400):i + 400]
    for m in re.finditer(r'["\'`][^"\'`]{0,200}(?:account_requests|connections|agentic|provisioning)[^"\'`]{0,200}["\'`]', seg):
        s = m.group(0)
        if s not in pats:
            pats.append(s)
for s in pats:
    print('STR:', s[:260], flush=True)

# 3. 所有 /api/v2/ 相关字符串(宽找 provisioning 家族)
print('\n=== /api/v2/ 全部端点字符串 ===', flush=True)
alls = set(re.findall(r'["\'`](/api/v[12]/[^"\'`]{3,120})["\'`]', src))
for s in sorted(alls):
    print(s, flush=True)
