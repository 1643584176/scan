# -*- coding: utf-8 -*-
# 盘点:533 路径 vs 已测脚本覆盖
import json, os, re, glob

d = os.path.dirname(os.path.abspath(__file__))
paths = json.load(open(os.path.join(d, '_q1_paths.json'), encoding='utf-8'))

# 1) 收集所有测试脚本与文档中的 API 路径出现
tested = set()
pat = re.compile(r'/api/[\w\-/${}.]+')
for f in glob.glob(os.path.join(d, '*.py')) + glob.glob(os.path.join(d, '*.md')):
    bn = os.path.basename(f)
    if bn in ('_q1_paths.json', '_ls_q1.py', '_ls_md.py'):
        continue
    try:
        txt = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in pat.findall(txt):
        tested.add(m)

# 2) 模糊匹配:path 模板（含 ${}）与已测字面路径
def gen_variants(tpl):
    """把 /api/foo/${x} 转成正则"""
    return re.sub(r'\\\$\{[^}]+\}', r'[^/]+', re.escape(tpl))

tested_norm = set()
for t in tested:
    # 去掉查询串
    t = t.split('?')[0].rstrip('.')
    tested_norm.add(t)

tested_re = [re.compile('^' + gen_variants(t) + '$') for t in tested_norm]

hit, miss = [], []
for p in sorted(paths.keys()):
    pn = p.split('?')[0]
    ok = any(r.match(pn) for r in tested_re)
    (hit if ok else miss).append(pn)

print('=== TOTAL:', len(paths), ' HIT:', len(hit), ' MISS:', len(miss))
print()
print('=== MISS (未在脚本/文档中出现),前 120:')
for p in miss[:120]:
    print(' ', p)
