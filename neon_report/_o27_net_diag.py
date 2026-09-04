# -*- coding: utf-8 -*-
"""网络诊断:console-stage vs nauth vs PG 连通性"""
import http.client, ssl, socket, time

ctx = ssl.create_default_context()

def probe(host, port=443, path='/', timeout=10):
    t0 = time.time()
    try:
        conn = http.client.HTTPSConnection(host, port, context=ctx, timeout=timeout)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0'})
        r = conn.getresponse()
        raw = r.read()[:80]
        conn.close()
        return 'ok st=%d %.1fs %s' % (r.status, time.time() - t0, raw.decode('utf-8', 'replace')[:60].replace('\n', ' '))
    except Exception as e:
        return 'ERR %.1fs %s' % (time.time() - t0, e)

for h, p in [('console-stage.neon.build', '/'), ('console-stage.neon.build', '/api/v2/projects'),
             ('neonauth.us-east-2.aws.neon.build', '/neondb/auth/jwks.json'),
             ('ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build', '/'),
             ('api.ipify.org', '/'), ('google.com', '/')]:
    print('%-50s %s' % (h, probe(h, 443, p)), flush=True)

# DNS 检查
for h in ['console-stage.neon.build', 'neonauth.us-east-2.aws.neon.build']:
    try:
        print('dns %s -> %s' % (h, socket.gethostbyname(h)), flush=True)
    except Exception as e:
        print('dns %s ERR %s' % (h, e), flush=True)
