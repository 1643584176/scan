# -*- coding: utf-8 -*-
"""搜历史脚本+md 里 transfer 相关痕迹"""
import glob, os

hits = {}
for pat in ['_*.py', '*.md']:
    for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), pat)):
        try:
            txt = open(f, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        if 'transfer' in txt.lower():
            lines = [l.strip()[:130] for l in txt.splitlines() if 'transfer' in l.lower()]
            hits[os.path.basename(f)] = lines[:8]
for f, lines in hits.items():
    print('=' * 20, f)
    for l in lines:
        print('  ', l)
