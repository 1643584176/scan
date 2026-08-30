# -*- coding: utf-8 -*-
"""查 e150 中 V20-V28 cell.api 访问通道 + J546 MITM 历史"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()

# 找 V20-V28 标记与 socket/通道相关行
for i, l in enumerate(lines):
    if re.search(r'V2[0-8][\s:：]|cell\.api|DrivesService|CreateSnapshot|23456|cell\.sock|vsock|unix socket|AF_UNIX|socket path|怎么访问|通道', l):
        print('%4d: %s' % (i, l[:500]))
        print()
