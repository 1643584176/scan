# -*- coding: utf-8 -*-
"""h1x45: bundle 里找 WebSocket/subscription 端点与协议"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
files = [r'D:\scan\h1kit\_h1x4_app.js', r'D:\scan\h1kit\_h1x4_vendor.js', r'D:\scan\h1kit\_h1x3_main.js', r'D:\scan\h1kit\_h1x3_constants.js']
pats = {
    'ws_url': r'wss?://[^"\'`\s]+',
    'sub_path': r'[/][a-zA-Z0-9_./-]*subscription[a-zA-Z0-9_./-]*',
    'ws_proto': r'graphql-ws|subscriptions-transport-ws',
    'ws_new': r'new WebSocket\([^)]{0,120}',
    'ws_link': r'WebSocketLink',
    'absinthe': r'absinthe|phoenix|channels?/[a-z_]+',
}
for f in files:
    try:
        t = open(f, encoding='utf-8', errors='ignore').read()
    except Exception as e:
        print(f, 'ERR', e); continue
    print('=====', f, f'({len(t)//1024}KB)')
    seen = set()
    for name, pat in pats.items():
        for m in re.finditer(pat, t):
            s = m.group(0)
            if s not in seen:
                seen.add(s)
                print(f'  [{name}] {s[:160]}')
