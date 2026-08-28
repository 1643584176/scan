# -*- coding: utf-8 -*-
"""提取历史会话中所有 Vercel API 端点调用(python 代码/curl)"""
import re, os

BASE = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history'
TARGETS = ['e1507845', 'd1c9a155', '558c85f7', '8b33948a', '494b74ea', '1a7a395a', '478d0b50', '465c8d42', '6a5402ab', '3d4619a8', '16ba677c']
OUT = r'D:\scan\skills\non-traditional-vuln-hunting\vercel_api_calls.txt'

lines = []
pat_url = re.compile(r'https?://api\.[^\s"\'\\,)\]]+')
pat_curl = re.compile(r'curl [^\n]{10,300}')
pat_req = re.compile(r'(urlopen|Request|url\s*=|endpoint\s*=)[^\n]{5,300}', re.I)

for sid in TARGETS:
    fp = os.path.join(BASE, sid, sid + '.jsonl')
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    hits = []
    for pat in (pat_url, pat_curl, pat_req):
        for m in pat.finditer(content):
            seg = content[max(0, m.start() - 120):m.end() + 150]
            seg = seg.replace('\\n', '\n').replace('\\"', '"').replace('\\u003c', '<').replace('\\u003e', '>')
            hits.append(seg)
    if hits:
        lines.append('################ %s (%d hits) ################' % (sid, len(hits)))
        for h in hits[:30]:
            lines.append('-----')
            lines.append(h[:450])

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('written:', OUT, len(lines), 'lines')
