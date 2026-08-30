# -*- coding: utf-8 -*-
"""解析 vda40 输出中的 data 字段 (debug)"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'F:\scan\skills\out\vda40_exec_fix_guest_20260830_150426.txt'
with open(path, 'rb') as f:
    raw = f.read()
t = raw.decode('utf-8', errors='replace')
lines = [l for l in t.splitlines() if l.strip().startswith('{')]
print('json lines:', len(lines))
for i, line in enumerate(lines):
    try:
        j = json.loads(line)
        if 'data' in j:
            print('--- data line %d ---' % i)
            print(j['data'])
    except Exception as e:
        print('line %d parse err: %s' % (i, e))
