# -*- coding: utf-8 -*-
"""h1x16: 提取全部 query operation 的顶层选择集字段(2空格缩进行)→ 根字段清单"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
pat = r'"(?:\\n\s*)?(?:query|mutation)\s+([A-Za-z0-9_]+)'
roots = {}
count = 0
for mm in re.finditer(pat, t):
    name = mm.group(1)
    i = mm.end()
    # 跳到 '{' 之后(参数可能多行)
    j = t.find('{', i)
    if j == -1 or j - i > 2000:
        continue
    seg = t[j:j+6000].replace('\\n', '\n')
    count += 1
    # 顶层字段:缩进为 2 空格的行;排除 fragment spread / 闭合括号
    for line in seg.split('\n'):
        m2 = re.match(r'^  ([a-zA-Z_][a-zA-Z0-9_]*)\s*(?::\s*([a-zA-Z_][a-zA-Z0-9_]*))?\s*(?:\(|\{|$)', line)
        if m2:
            f = m2.group(2) or m2.group(1)
            if f not in ('query', 'mutation'):
                roots.setdefault(f, set()).add(name)
        if '}' in line and not line.strip().startswith('}'):
            # 顶层选择集结束(遇到仅 '}' 行前内容已足够,不 break,继续无妨)
            pass

print('operations parsed:', count)
print('\n=== ROOT FIELDS ===')
for f, qs in sorted(roots.items(), key=lambda x: -len(x[1])):
    ql = sorted(qs)
    print(f'{f:35s} {len(ql):4d}  {ql[:4]}')
