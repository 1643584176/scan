# -*- coding: utf-8 -*-
"""1. 查 OL.TEAM 枚举值 2. 查 FILE_A 分享设置(file_metadata + 权限 API)"""
import re, json, time, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_B, FILE_A

# 1. OL.TEAM 枚举
d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()
for pat in [r'OL\s*=\s*\{[^}]{0,200}\}', r'OL:\{?[^;]{0,120}TEAM[^;]{0,60}']:
    for m in list(re.finditer(pat, d))[:3]:
        print('ENUM:', m.group(0)[:200])
# TEAM:"..." 形式
for m in list(re.finditer(r'TEAM\s*:\s*"[a-z_]+"', d))[:10]:
    print('TEAM val:', m.group(0))
for m in list(re.finditer(r'ORG\s*:\s*"[a-z_]+"', d))[:10]:
    print('ORG val:', m.group(0))

print()
# 2. FILE_A 分享设置
TSID = 'mk' + str(int(time.time() * 1000))[-14:]
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('www.figma.com', context=ctx, timeout=30)
for path in ['/api/file_metadata/%s' % FILE_A,
             '/api/files/%s/permissions' % FILE_A,
             '/api/files/%s' % FILE_A]:
    conn.request('GET', path, headers={
        'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
        'Cookie': COOKIE_B, 'tsid': TSID, 'x-csrf-bypass': 'yes',
        'x-figma-client-version': '24850ed350d86c5466f8b775996885ec28db9f19',
        'x-figma-user-id': UID_B, 'origin': 'https://www.figma.com'})
    resp = conn.getresponse()
    body = resp.read()
    enc = resp.getheader('Content-Encoding')
    if enc == 'br':
        body = brotli.decompress(body)
    elif enc == 'gzip':
        body = gzip.decompress(body)
    print('---', path, resp.status)
    txt = body.decode('utf-8', 'ignore')
    print(txt[:900])
    print()
