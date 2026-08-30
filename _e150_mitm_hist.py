# -*- coding: utf-8 -*-
"""查 e150 中 J544 MITM + J548-J565 init.sock/签名/23456 细节"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()

for i, l in enumerate(lines):
    if re.search(r'J54[0-9]|J55[0-9]|MITM|mitm|init\.sock|x-signature|timestamp|signature|重放|replay', l):
        print('%4d: %s' % (i, l[:600]))
        print()
