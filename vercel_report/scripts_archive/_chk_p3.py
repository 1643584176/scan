# -*- coding: utf-8 -*-
"""分析 _v105p3_local.txt: Service 名 / connect 包 / 方法名"""
import io, re

lines = io.open('_v105p3_local.txt', encoding='utf-8', errors='replace').read().splitlines()
svc = set()
conn = set()
for l in lines:
    s = l[2:]  # 去 "K " 前缀
    if 'Service' in s:
        svc.add(s)
    if 'connect' in s:
        conn.add(s)
print('=== Service-related (%d) ===' % len(svc))
for s in sorted(svc):
    print(' ', s[:150])
print()
print('=== connect pkg (%d) ===' % len(conn))
for s in sorted(conn):
    print(' ', s[:150])
