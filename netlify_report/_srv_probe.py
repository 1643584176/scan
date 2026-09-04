# -*- coding: utf-8 -*-
"""探测内部域名可达性(DNS + HTTPS)"""
import socket, http.client, ssl, time

hosts = [
    'jigsaw.services-prod.nsvcs.net',
    'socketeer.services.netlify.com',
    'api-create.services.netlify.com',
    'identeer.services.netlify.com',
    'analytics.services.netlify.com',
    'lambda-events.services.netlify.com',
    'jigsaw.services.netlify.com',
    'jigsaw.nsvcs.net',
]
ctx = ssl.create_default_context()
for h in hosts:
    try:
        ip = socket.gethostbyname(h)
    except Exception as e:
        print('%-42s DNS FAIL %s' % (h, str(e)[:50]))
        continue
    # 尝试 https 根路径
    try:
        conn = http.client.HTTPSConnection(h, context=ctx, timeout=8)
        conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        r = conn.getresponse()
        raw = r.read(300)
        st = r.status
        conn.close()
        print('%-42s %-16s %s %s' % (h, ip, st, raw[:80].decode('utf-8', 'replace').replace('\n', ' ')))
    except Exception as e:
        print('%-42s %-16s CONN FAIL %s' % (h, ip, str(e)[:60]))
