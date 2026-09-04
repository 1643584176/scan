# -*- coding: utf-8 -*-
"""通用: JSON 解析 run 输出, 打印完整 stdout. 用法: python _jsonout.py <file>"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

path = sys.argv[1]
lines = open(path, 'rb').read().decode('utf-8', errors='replace')
for ln in lines.splitlines():
    if not ln.strip():
        continue
    try:
        j = json.loads(ln)
        if 'data' in j:
            print(j['data'], end='')
    except Exception:
        pass
