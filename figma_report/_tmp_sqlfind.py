# -*- coding: utf-8 -*-
"""找 versions/{fk} 那条 SQL 的文档证据: 绑定位/file_key 相关段落"""
import os, io, re

DIR = r'D:/scan/figma_report'
pats = [re.compile(r'绑定位'), re.compile(r'file_key\s*='), re.compile(r'WHERE\s+file_key'),
        re.compile(r'\$1'), re.compile(r'SELECT')]

# 1. 扫 md 文档
for fn in sorted(os.listdir(DIR)):
    if not fn.endswith('.md'):
        continue
    txt = io.open(os.path.join(DIR, fn), encoding='utf-8', errors='ignore').read()
    lines = txt.split('\n')
    hits = []
    for i, ln in enumerate(lines):
        for p in pats:
            if p.search(ln):
                hits.append((i + 1, ln.strip()[:180]))
                break
    if hits:
        print('#' * 10, fn, '(%d hits)' % len(hits))
        for ln_no, s in hits[:25]:
            print('  %5d| %s' % (ln_no, s))
        print()

# 2. 扫 py 脚本里的 SQL 片段
print('=' * 30, 'py scripts with SQL-ish strings')
for fn in sorted(os.listdir(DIR)):
    if not fn.startswith('_') or not fn.endswith('.py'):
        continue
    try:
        txt = io.open(os.path.join(DIR, fn), encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'[^\n]*(?:FROM |INSERT |UPDATE |DELETE FROM |SELECT )[\w*][^\n]{10,200}', txt):
        s = m.group(0).strip()
        print('%s: %s' % (fn, s[:200]))
