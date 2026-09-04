# -*- coding: utf-8 -*-
"""调用 probe10 并保存输出"""
import http.client, ssl, json, sys

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('sec-b-08v4pk.netlify.app', context=ctx, timeout=120)
conn.request('GET', '/.netlify/functions/probe10', headers={'Accept': 'application/json'})
r = conn.getresponse()
raw = r.read()
print('status:', r.status)
conn.close()
if r.status != 200:
    print(raw[:500].decode('utf-8', 'replace'))
    sys.exit(1)
open(r'D:\scan\netlify_report\_probe10_out.json', 'wb').write(raw)
d = json.loads(raw)
print('resolv:', d.get('resolv'))
print('hosts:', d.get('hosts'))
print('route:', d.get('route'))
print('arp:', d.get('arp'))
print('envKeys:', json.dumps(d.get('envKeys'))[:800])
print('dns:', json.dumps(d.get('dns'))[:1500])
print('tcpConn:', (d.get('tcpConn') or '')[:1200])
