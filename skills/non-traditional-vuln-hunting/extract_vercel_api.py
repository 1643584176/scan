# -*- coding: utf-8 -*-
"""从历史会话中提取 Vercel Sandbox API 细节"""
import os, re, json, glob

BASE = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history'
KEY = 'api.vercel.com'

files = glob.glob(os.path.join(BASE, '*', '*.jsonl'))
for fp in sorted(files, key=lambda p: os.path.getmtime(p), reverse=True)[:12]:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        continue
    if KEY not in content:
        continue
    # 提取 URL 片段
    urls = set(re.findall(r'https?://[^\s"\'\\,]+', content))
    urls = {u for u in urls if 'vercel.com' in u}
    mtime = os.path.getmtime(fp)
    import datetime
    ts = datetime.datetime.fromtimestamp(mtime).strftime('%m-%d %H:%M')
    print('=== %s (%s) %dKB' % (os.path.basename(os.path.dirname(fp)), ts, os.path.getsize(fp)//1024))
    for u in sorted(urls)[:15]:
        print('   ', u[:150])
