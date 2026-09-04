# -*- coding: utf-8 -*-
"""1) 检查 B 站点函数存活 2) int-api/functions.internal 服务指纹"""
import http.client, ssl, json, sys

ctx = ssl.create_default_context()

# 1. 旧函数存活检查
for fn in ['probe3', 'probe9', 'probe-log', 'probe10']:
    try:
        conn = http.client.HTTPSConnection('sec-b-08v4pk.netlify.app', context=ctx, timeout=15)
        conn.request('GET', '/.netlify/functions/%s' % fn, headers={'Accept': 'application/json'})
        r = conn.getresponse()
        raw = r.read(150)
        st = r.status
        conn.close()
        print('%-10s %s %s' % (fn, st, raw[:100].decode('utf-8', 'replace').replace('\n', ' ')))
    except Exception as e:
        print('%-10s ERR %s' % (fn, str(e)[:60]))
print()

# 2. int-api / functions.internal 指纹
for h in ['int-api.netlify.com', 'functions.internal.netlify.com']:
    try:
        conn = http.client.HTTPSConnection(h, context=ctx, timeout=15)
        conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        r = conn.getresponse()
        raw = r.read(200)
        st = r.status
        srv = r.getheader('Server', '')
        conn.close()
        print('%-38s %s srv=%s %s' % (h, st, srv, raw[:120].decode('utf-8', 'replace').replace('\n', ' ')))
    except Exception as e:
        print('%-38s ERR %s' % (h, str(e)[:80]))
