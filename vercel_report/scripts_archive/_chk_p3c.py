# -*- coding: utf-8 -*-
"""p3 深挖: metrics / socket 路径 / 其他服务线索"""
import io, re

lines = io.open('_v105p3_local.txt', encoding='utf-8', errors='replace').read().splitlines()
kw = ['metrics', 'Metrics', '23456', 'listen', 'Listen', 'sock', '.sock', 'http', 'HTTP', 'health', 'Health',
      'debug', 'Debug', 'pprof', 'Pprof', 'grpc', 'Grpc', 'GRPC', 'ttrpc', 'host', 'Host']
seen = set()
for l in lines:
    s = l[2:]
    if any(k in s for k in kw) and not any(x in s for x in ('Request', 'Response', 'EntryR', 'func', 'WithLog', 'WithScope', 'OnceValue', 'deferwrap')):
        key = s[:120]
        if key not in seen:
            seen.add(key)
            print(s[:160])
