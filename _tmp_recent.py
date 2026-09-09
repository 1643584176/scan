# -*- coding: utf-8 -*-
"""找出 2026-09-06 以来修改过的进度类文件 (md/txt/json),排除已归档 report 目录"""
import os, time

EXCL = ('.venv', '.git', '.idea', 'figma_report', 'netlify_report', 'neon_report',
        'vercel_report', 'box_report', 'eternal_report', 'faraday_report',
        'launchdarkly_report', 'matomo_report', 'mergify_report', 'shopify_report',
        'supabase_report', 'wolt_report', 'h1kit', 'skills', '经验', '__pycache__')

CUTOFF = time.mktime(time.strptime('2026-09-06', '%Y-%m-%d'))
res = []
for dp, dn, fn in os.walk('.'):
    dn[:] = [d for d in dn if d not in EXCL and not d.startswith('_')]
    for f in fn:
        if not f.endswith(('.md', '.txt', '.json')):
            continue
        p = os.path.join(dp, f)
        st = os.stat(p)
        if st.st_mtime > CUTOFF:
            res.append((st.st_mtime, p))
res.sort(reverse=True)
for m, p in res[:40]:
    print(time.strftime('%m-%d %H:%M', time.localtime(m)), p)
