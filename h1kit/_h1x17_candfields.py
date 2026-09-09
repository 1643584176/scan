# -*- coding: utf-8 -*-
"""h1x17: 定位候选根字段的真实用法(2空格缩进 + 括号/花括号)+ 所属 operation"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 候选根字段
cands = ['me','user','users','team','teams','report','reports','activities','hacktivity',
         'notifications','inboxes','messages','bounties','weaknesses','search','report_feed',
         'recent_reports','opportunities','sessions','todos','organization','organizations',
         'duplicate_suggestions','related_vulnerability_reports','assets','programs',
         'report_templates','feed','activity','timeline']

# 形态:  \n  field(...) 或 \n  field {  (2空格)
pat = re.compile(r'\\n  (%s)(\s*[\(\{])' % '|'.join(cands))
found = {}
for m in pat.finditer(t):
    f = m.group(1)
    i = m.start()
    # 找所属 operation:往前找最近的 query/mutation 名
    head = t[max(0, i-8000):i]
    ops = re.findall(r'(?:query|mutation)\s+([A-Za-z0-9_]+)', head)
    op = ops[-1] if ops else '?'
    # 往后看 120 字符的字段形状
    shape = t[m.end()-1:m.end()+150].replace('\\n', ' ')
    found.setdefault(f, []).append((op, shape[:150]))

for f, lst in sorted(found.items()):
    print(f'=== {f} ({len(lst)}) ===')
    seen = set()
    for op, shape in lst[:6]:
        key = op
        if key in seen: continue
        seen.add(key)
        print(f'  {op:40s} {shape}')
