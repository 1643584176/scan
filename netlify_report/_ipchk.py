# -*- coding: utf-8 -*-
import http.client, ssl
ctx = ssl.create_default_context()
for h in ('api.ipify.org', 'api.netlify.com', 'sec-b-08v4pk.netlify.app'):
    try:
        c = http.client.HTTPSConnection(h, timeout=15, context=ctx)
        c.request('GET', '/')
        r = c.getresponse()
        body = r.read()[:200]
        print(h, r.status, body, flush=True)
        c.close()
    except Exception as e:
        print(h, 'EXC', repr(e)[:150], flush=True)
