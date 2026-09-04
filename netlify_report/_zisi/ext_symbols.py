# -*- coding: utf-8 -*-
"""本地逆向:符号表(telemetry_api 相关)+ 可疑短路径串 + http 相关字符串"""
import re

data = open(r'D:\scan\netlify_report\_ext_binary.bin', 'rb').read()

# 1. telemetry_api / repo 符号(函数名)
print('=== telemetry_api symbols ===')
syms = set()
for m in re.finditer(rb'[A-Za-z0-9_\.\-\/]{6,120}telemetry_api[A-Za-z0-9_\.\-\/]{0,80}', data):
    t = m.group(0).decode('ascii', 'replace')
    if len(t) < 150:
        syms.add(t)
for s in sorted(syms)[:50]:
    print(' ', s)

print()
print('=== repo/ symbols ===')
syms2 = set()
for m in re.finditer(rb'repo/[a-z_/]+\.go:[0-9]+', data):
    syms2.add(m.group(0).decode('ascii', 'replace'))
for s in sorted(syms2)[:60]:
    print(' ', s)

# 2. 可疑短路径串(含 / 不含空格、不含 .go / 源码路径特征)
print()
print('=== short path-like strings ===')
paths = set()
for m in re.finditer(rb'[\x20-\x7e]{3,80}', data):
    t = m.group(0).decode('ascii', 'replace')
    if '/' not in t:
        continue
    if '.go' in t or '.s' in t or '.md' in t or t.startswith('/home/') or t.startswith('/usr/') or t.startswith('/var/') or t.startswith('/etc/') or t.startswith('/proc/') or t.startswith('/sys/') or t.startswith('/dev/') or t.startswith('/opt/') or t.startswith('/tmp/') or t.startswith('/var/') or t.startswith('/root/') or t.startswith('/lib') or 'runtime' in t and 'go' in t:
        continue
    if ' ' in t or '\t' in t:
        continue
    if any(c in t for c in '(){}[]<>;=*'):
        continue
    if len(t) < 70:
        paths.add(t)
for p in sorted(paths)[:150]:
    print(' ', p)
