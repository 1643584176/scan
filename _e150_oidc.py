# -*- coding: utf-8 -*-
"""查 e150 历史中 J509 与 OIDC 相关内容"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()

for i, l in enumerate(lines):
    if '509' in l or 'oidc' in l.lower() or 'OIDC' in l:
        print('%4d: %s' % (i, l[:800]))
        print()
