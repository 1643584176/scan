# -*- coding: utf-8 -*-
import json

f = open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\92f41401\92f41401.jsonl',
         encoding='utf-8', errors='replace')
lines = f.readlines()
out = []
for i, ln in enumerate(lines):
    try:
        o = json.loads(ln)
    except Exception:
        continue
    if o.get('role') != 'user':
        continue
    c = o.get('message', {}).get('content')
    if isinstance(c, list):
        parts = []
        for x in c:
            if isinstance(x, dict) and x.get('type') == 'text':
                parts.append(x.get('text', ''))
        joined = ' '.join(parts)
    else:
        joined = str(c)
    joined = joined.strip()
    # 提取 user_query 标签内文本
    import re
    m = re.search(r'<user_query>(.*?)</user_query>', joined, re.S)
    if m:
        q = m.group(1).strip().replace('\n', ' ')
        out.append((i, q))
    elif joined and not joined.startswith('<'):
        out.append((i, joined[:150]))
for i, q in out:
    print(i, '|', q[:200])
