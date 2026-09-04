# -*- coding: utf-8 -*-
"""A 站点 probe3 当前 env token(对比 B 新 deploy 5c6d529f)"""
import http.client, ssl, json, sys, re

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=60)
conn.request('GET', '/.netlify/functions/probe3?mode=env', headers={'Accept': 'application/json'})
r = conn.getresponse()
raw = r.read()
st = r.status
conn.close()
print('status:', st)
if st == 200:
    txt = raw.decode('utf-8', 'replace')
    for m in re.finditer(r'NETLIFY_FUNCTIONS_TOKEN["\']?\s*[:=]\s*["\']([^"\']+)', txt):
        print('B site token:', m.group(1))
    if 'NETLIFY_FUNCTIONS_TOKEN' not in txt:
        print('no token in response, head:', txt[:300])
else:
    print(raw[:300].decode('utf-8', 'replace'))
