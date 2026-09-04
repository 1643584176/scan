# -*- coding: utf-8 -*-
"""查找今日探测脚本的 driver 与输出文件"""
import os, re, datetime

roots = [r'F:\scan\skills\non-traditional-vuln-hunting', r'F:\scan\out', r'F:\scan\reports', r'F:\scan\vercel_report']
pat = re.compile(r'vsock|celld|host_probe|hp2|pid1|udp|fast|celld2', re.I)
today = datetime.datetime(2026, 8, 29).timestamp()

print('=== 今日涉及 vsock/celld/host_probe/pid1/udp 的文件 ===')
seen = set()
for root in roots:
    for dirpath, dirnames, filenames in os.walk(root):
        if '__pycache__' in dirpath or '.venv' in dirpath or '.git' in dirpath:
            continue
        for f in filenames:
            p = os.path.join(dirpath, f)
            if pat.search(f) and os.path.getmtime(p) >= today:
                if p in seen: continue
                seen.add(p)
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d %H:%M')
                print(f'  [{mt}] {p}  ({os.path.getsize(p)} B)')

print()
print('=== 输出目录 out/ 全部内容 ===')
for f in sorted(os.listdir(r'F:\scan\out')):
    p = os.path.join(r'F:\scan\out', f)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d %H:%M')
    print(f'  [{mt}] {f}  ({os.path.getsize(p)} B)')
