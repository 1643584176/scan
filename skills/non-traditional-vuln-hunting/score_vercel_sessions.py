# -*- coding: utf-8 -*-
"""搜索历史会话中 Vercel sandbox API 端点与调用代码"""
import os, re, glob, datetime

BASE = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history'
KEYWORDS = ['/v1/sandbox', 'sandbox', 'sbx_', 'team_GIy1SZ', 'exp_j', 'x-vercel', 'Authorization']

files = glob.glob(os.path.join(BASE, '*', '*.jsonl'))
scores = []
for fp in files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        continue
    cnt = sum(content.count(k) for k in KEYWORDS)
    if cnt > 0:
        mtime = os.path.getmtime(fp)
        ts = datetime.datetime.fromtimestamp(mtime).strftime('%m-%d %H:%M')
        scores.append((cnt, os.path.basename(os.path.dirname(fp)), ts, os.path.getsize(fp)//1024))

scores.sort(reverse=True)
for cnt, sid, ts, kb in scores[:12]:
    print('%4d hits  %s (%s) %dKB' % (cnt, sid, ts, kb))
