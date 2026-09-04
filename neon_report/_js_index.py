# -*- coding: utf-8 -*-
"""下载 console-stage 首页 JS bundle 列表,准备 grep createProject 调用"""
import http.client, ssl, re, sys
sys.path.insert(0, r'D:\scan\neon_report')
from _neon_creds_stage import cookie_str, API_HOST

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
r = conn.getresponse(); body = r.read(); conn.close()
txt = body.decode('utf-8', 'replace')

scripts = re.findall(r'<script[^>]+src="([^"]+)"', txt)
print('scripts:')
for s in scripts:
    print(' ', s[:150])
# 也找 module preload / assets
assets = re.findall(r'href="(/assets/[^"]+)"', txt)
print('assets count:', len(assets))
