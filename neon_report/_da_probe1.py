# -*- coding: utf-8 -*-
"""Data API 首次探测:根/OpenAPI/匿名访问面"""
import http.client, ssl, json, sys
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
DA = 'ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build'
BASE = '/neondb/rest/v1'

def get(path, hdr=None):
    try:
        conn = http.client.HTTPSConnection(DA, context=ctx, timeout=30)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        if hdr: h.update(hdr)
        conn.request('GET', BASE + path, headers=h)
        r = conn.getresponse(); raw = r.read()
        st = r.status; conn.close()
        return st, raw
    except Exception as e:
        return 0, str(e).encode()

for p, h in [('/', None), ('/', {'Accept': 'application/openapi+json'}),
             ('/', {'Accept': 'text/html'}),
             ('/openapi.json', None)]:
    st, raw = get(p, h)
    print('== GET %s hdr=%s -> %d' % (p, (h or {}).get('Accept', '-'), st))
    print('   ', raw[:500])
