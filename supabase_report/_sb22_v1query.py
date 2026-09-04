# -*- coding: utf-8 -*-
"""v1 database/query 通道测试 (内部连接?) + pg-meta 辅助端点探针"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag=''):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Authorization": "Bearer " + BEARER_JWT}
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(2000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:600]))
        c.close()
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))

# v1 database/query (带 read_only 参数)
req('POST', '/v1/projects/%s/database/query' % PROJECT_REF,
    {"query": "select current_user, version()", "read_only": True}, 'v1-query-ro')
req('POST', '/v1/projects/%s/database/query/read-only' % PROJECT_REF,
    {"query": "select current_user"}, 'v1-query-ro2')
# pg-meta 可能存在的辅助端点 (猜路径)
for p in ['/platform/pg-meta/%s/connection' % PROJECT_REF,
          '/platform/projects/%s/connection-string' % PROJECT_REF,
          '/platform/projects/%s/connection' % PROJECT_REF,
          '/platform/projects/%s/database/connection' % PROJECT_REF]:
    req('GET', p, None, 'conn-probe')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb22_v1query.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out))
