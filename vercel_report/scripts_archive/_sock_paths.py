# -*- coding: utf-8 -*-
"""搜索 e150 中 containerd/cell.sock 连接路径与 V27-V29 执行细节"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()

# 搜 socket 路径引用
pats = [r'cell\.sock', r'containerd\.sock', r'/mnt/vda', r'ctr ', r'v27', r'v28', r'v29', r'V27', r'V28', r'V29',
        r'unix.*connect|connect.*unix', r'socat|nc -U|ncat']
for i, l in enumerate(lines):
    if re.search(r'containerd\.sock|/mnt/vda|ctr |cell\.sock', l, re.I):
        print('%4d: %s' % (i, l[:500]))
        print()
