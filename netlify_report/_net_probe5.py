# -*- coding: utf-8 -*-
"""Netlify 侦察 5:精确提取 URL/GraphQL/接口模式(ASCII 输出)"""
import os, re

jsdir = r'D:\scan\netlify_report\_js'
files = {}
for f in os.listdir(jsdir):
    if f.endswith('.js'):
        files[f] = open(os.path.join(jsdir, f), encoding='utf-8', errors='ignore').read()

def show(fname, pat, maxn=8, w=140):
    txt = files[fname]
    out = []
    for m in re.finditer(pat, txt):
        i = m.start()
        out.append(txt[max(0, i - 50): i + w].replace('\n', ' '))
        if len(out) >= maxn:
            break
    return out

print('=== api.netlify.com refs ===')
for f, t in files.items():
    if 'api.netlify.com' in t:
        print('[' + f + ']')
        for m in re.finditer(r'[a-zA-Z0-9_$.\-]{0,40}["\'`]?https?://api\.netlify\.com[^"\'\s,)]{0,80}', t):
            i = m.start()
            print('   ', t[max(0, i - 60): i + 120].replace('\n', ' ')[:170])
            break

print()
print('=== graphql refs ===')
for f, t in files.items():
    for m in re.finditer(r'["\']/(?:api/)?graphql[^"\']{0,40}["\']|graphql\s*[:=]\s*["\'][^"\']+["\']', t):
        i = m.start()
        print('[' + f + ']', t[max(0, i - 60): i + 100].replace('\n', ' ')[:160])
        break

print()
print('=== /api/v2/ refs ===')
for f, t in files.items():
    for m in re.finditer(r'/api/v2/[a-zA-Z0-9_\-${}.:/]+', t):
        print('[' + f + ']', m.group(0)[:100])
        break

print()
print('=== netlify.app / netlify.com custom domain patterns ===')
for f, t in files.items():
    for m in re.finditer(r'https?://[a-z0-9\-]+\.netlify\.(?:app|com)[^"\'\s]{0,60}', t):
        print('[' + f + ']', m.group(0)[:120])
        break
