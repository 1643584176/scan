# -*- coding: utf-8 -*-
"""JSON 解析 deep90 输出, 还原完整 stdout"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

lines = open(r'F:\scan\skills\out\deep33090_guest_20260829_134434.txt', 'rb').read().decode('utf-8', errors='replace')
out = []
for ln in lines.splitlines():
    if not ln.strip():
        continue
    try:
        j = json.loads(ln)
        if 'data' in j:
            out.append(j['data'])
    except Exception:
        pass

full = ''.join(out)
print(full)
