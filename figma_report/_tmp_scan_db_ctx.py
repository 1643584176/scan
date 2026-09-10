# -*- coding: utf-8 -*-
"""扫描今日输出中数据库方向相关线索"""
import glob, io, re, os
os.chdir('D:/scan/figma_report')
pats = ['supabase', 'postgres', 'postgrest', 'sql', 'database', 'db_', ' rds', 'aurora', 'cloudsql',
        'collection', 'cms', 'sqlite', 'hasura', 'prisma', 'drizzle', 'kysely']
files = sorted(glob.glob('_q*_out.txt') + glob.glob('_r*_out.txt') +
               glob.glob('_q*.py') + glob.glob('_figma_q*.py') + glob.glob('_figma_r*.py'))
hits = {}
for f in files:
    try:
        t = io.open(f, encoding='utf-8', errors='replace').read().lower()
    except Exception:
        continue
    for p in pats:
        if p in t:
            hits.setdefault(p, []).append(f)
for p in pats:
    fs = hits.get(p)
    if fs:
        print(f'{p:12s} -> {len(fs)} files: {fs[:10]}')
    else:
        print(f'{p:12s} -> 0')
