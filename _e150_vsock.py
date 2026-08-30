# -*- coding: utf-8 -*-
"""查 e150 J526 vsock 1024/1025/1026 探测细节 + io_uring 绕过方法"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()

for i, l in enumerate(lines):
    if re.search(r'J52[0-9]|1024|1025|1026|io_uring|AF_VSOCK|vsock', l):
        print('%4d: %s' % (i, l[:700]))
        print()
