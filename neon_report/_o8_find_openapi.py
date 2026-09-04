# -*- coding: utf-8 -*-
"""提取 OpenAPI Functions tag 路径+schema(定位 openapi 文件)"""
import glob, json, os

cands = []
for root in ['D:/scan/neon_report', 'D:/scan']:
    for p in glob.glob(root + '/**/*openapi*.json', recursive=True):
        cands.append(p)
    for p in glob.glob(root + '/**/*openapi*.yaml', recursive=True):
        cands.append(p)
    for p in glob.glob(root + '/**/*swagger*.json', recursive=True):
        cands.append(p)
print('openapi candidates:')
for p in cands:
    print(' ', p, os.path.getsize(p) if os.path.exists(p) else '')
