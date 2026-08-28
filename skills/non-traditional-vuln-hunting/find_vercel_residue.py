# -*- coding: utf-8 -*-
"""搜索工作区中 Vercel 相关残留文件(TOKEN/脚本/配置)"""
import os

ROOT = r'D:\scan'
SKIP = {'.venv', '.git', 'notion_report'}
PATTERNS = ['vercel', 'team_GIy1SZ', 'prj_iyw2xfj', 'sbx_', 'exp_j3']
EXTS = ('.py', '.txt', '.json', '.md', '.sh', '.env', '.cfg', '.ini')

hits = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    for fn in filenames:
        if not fn.endswith(EXTS):
            continue
        p = os.path.join(dirpath, fn)
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        for pat in PATTERNS:
            if pat in content:
                hits.append((p, pat))
                break

for p, pat in hits:
    print('[%s] %s' % (pat, p))
print('--- total:', len(hits))
