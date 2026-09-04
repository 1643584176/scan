# -*- coding: utf-8 -*-
"""继续 day-plan-0829：检查 J546 MITM 捕获与 exp332/V29 状态"""
import os, re

D = r'F:\scan\skills\non-traditional-vuln-hunting'
files = sorted(os.listdir(D))
print('=== 与 J5/J6/MITM/cap 相关的文件 ===')
for f in files:
    if re.search(r'j5|j6|mitm|cap|resp|sock|snoop', f, re.I):
        p = os.path.join(D, f)
        print(f'  {f}  ({os.path.getsize(p)} B)')

print()
print('=== 最近的 30 个文件（按修改时间）===')
recent = sorted(files, key=lambda f: os.path.getmtime(os.path.join(D, f)), reverse=True)[:30]
for f in recent:
    p = os.path.join(D, f)
    import datetime
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d %H:%M')
    print(f'  {mt}  {f}  ({os.path.getsize(p)} B)')

print()
print('=== e150_tail.txt 内容 ===')
with open(os.path.join(D, 'e150_tail.txt'), 'r', encoding='utf-8', errors='replace') as fh:
    print(fh.read()[:3000])
