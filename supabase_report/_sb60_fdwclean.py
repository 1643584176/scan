# -*- coding: utf-8 -*-
"""补清理: drop postgres_fdw"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
def q(sql, tag):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(3000).decode('utf-8', errors='replace')
        print('[%s] %s | %s' % (tag, r.status, b[:800]))
        c.close()
    except Exception as e:
        print('[%s] ERR %s' % (tag, e))

q("drop extension if exists postgres_fdw cascade;", 'drop-fdw')
q("select extname from pg_extension where extname='postgres_fdw';", 'recheck')
