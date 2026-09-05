# -*- coding: utf-8 -*-
import http.client, ssl
ctx = ssl.create_default_context()
for h, p in (('1.1.1.1', '/cdn-cgi/trace'), ('httpbin.org', '/ip'), ('ifconfig.me', '/ip')):
    try:
        c = http.client.HTTPSConnection(h, timeout=15, context=ctx)
        c.request('GET', p)
        r = c.getresponse()
        print(h, r.status, r.read()[:300], flush=True)
        c.close()
    except Exception as e:
        print(h, 'EXC', repr(e)[:120], flush=True)
