# -*- coding: utf-8 -*-
"""本地逆向:关键字原始字节上下文(URL/token/路径构造)"""
import re

data = open(r'D:\scan\netlify_report\_ext_binary.bin', 'rb').read()

def ctx(kw, before=400, after=500, limit=8):
    print('=== %s ===' % kw)
    cnt = 0
    for m in re.finditer(re.escape(kw.encode()), data):
        c = data[max(0, m.start() - before):m.start() + after]
        c = re.sub(rb'[^\x20-\x7e]', b'|', c).decode('ascii', 'replace')
        print('---')
        print(c)
        cnt += 1
        if cnt >= limit:
            break
    if cnt == 0:
        print('(none)')

for kw in ['https://', 'lambda-events', 'services.netlify', 'NETLIFY_FUNCTIONS_TOKEN', '/v1/', 'api/v1', 'extension/register', 'telemetry/register', 'event/next']:
    ctx(kw)
