# -*- coding: utf-8 -*-
"""本地逆向 _ext_binary.bin:提取所有可打印字符串(含上下文)"""
import re, sys

data = open(r'D:\scan\netlify_report\_ext_binary.bin', 'rb').read()
print('file size:', len(data))

# 1. 全量可打印字符串(>=5)
strs = re.findall(rb'[\x20-\x7e]{5,}', data)
print('total strings:', len(strs))

def sfind(kw, before=300, after=400, limit=10):
    """找关键字上下文(可打印化)"""
    res = []
    for m in re.finditer(re.escape(kw.encode()), data):
        ctx = data[max(0, m.start() - before):m.start() + after]
        ctx = re.sub(rb'[^\x20-\x7e]', b'.', ctx).decode('ascii', 'replace')
        res.append(ctx)
        if len(res) >= limit:
            break
    return res

# 2. URL 全量
print()
print('=== URLs ===')
urls = set()
for s in strs:
    if b'://' in s and b' ' not in s.strip():
        for u in re.findall(rb'[a-z]+://[^\x00-\x20]+', s):
            if len(u) < 250:
                urls.add(u.decode('ascii', 'replace'))
for u in sorted(urls)[:60]:
    print(' ', u)

# 3. 路径类字符串(含 / 且可能为路径)
print()
print('=== path-like (from strings) ===')
paths = set()
for s in strs:
    t = s.decode('ascii', 'replace')
    if t.startswith('/') and 2 < len(t) < 120 and not t.startswith('//') and ' ' not in t:
        paths.add(t)
    elif '/' in t and t.startswith(('v1/', 'v2/', 'api/', 'event', 'record', 'batch', 'telemetry')) and len(t) < 120 and ' ' not in t:
        paths.add(t)
for p in sorted(paths)[:80]:
    print(' ', p)
