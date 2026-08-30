# -*- coding: utf-8 -*-
"""检查 md 文件中的非 ASCII 字符（中文残留）"""
import re, sys

files = [
    r'F:\scan\vercel_report\fw_vpc\H1-sandbox-custom-policy-vpc-bypass-submission.md',
    r'F:\scan\vercel_report\fw_vpc\H1-sandbox-custom-policy-vpc-bypass.md',
]
for f in files:
    txt = open(f, encoding='utf-8').read()
    cjk = re.findall(r'[\u4e00-\u9fff]+', txt)
    print(f.split('\\')[-1], 'CJK count:', len(cjk))
    if cjk:
        for m in cjk[:20]:
            print('  ', m)
