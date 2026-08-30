# -*- coding: utf-8 -*-
"""解析 cmd API 输出 JSONL, 提取 data 流"""
import sys, json

fn = sys.argv[1]
for ln in open(fn, encoding='utf-8', errors='replace'):
    ln = ln.strip()
    if not ln:
        continue
    try:
        d = json.loads(ln)
    except Exception:
        print(ln)
        continue
    if 'data' in d:
        print(d['data'], end='')
    elif d.get('command', {}).get('exitCode') is not None and 'data' not in d:
        pass
