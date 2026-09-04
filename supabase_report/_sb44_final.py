# -*- coding: utf-8 -*-
"""DB 细测 G: storage ACL 面 + org members + 连接信息面"""
import http.client, ssl, json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF, ORG_SLUG, USER_ID

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
        b = r.read(8000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:3000]))
        c.close()
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))

def q(sql, tag, maxb=20000):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(maxb).decode('utf-8', errors='replace')
        out.append('### [%s] (%.1fs)\n%s | %s' % (tag, time.time() - t0, r.status, b[:16000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. storage 表 ACL (buckets/objects/migrations)
q("""select c.relname, pg_get_userbyid(c.relowner) owner, c.relacl::text acl, c.relrowsecurity rls,
  has_table_privilege('anon', c.oid, 'SELECT') anon_sel,
  has_table_privilege('authenticated', c.oid, 'SELECT') au_sel
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='storage' and c.relkind='r' order by 1;""", "storage-acl")
# 2. org members (协作面现状)
req('GET', '/v1/organizations/%s/members' % ORG_SLUG, None, 'org-members')
req('GET', '/v1/organizations/%s' % ORG_SLUG, None, 'org-detail')
# 3. 项目连接/数据库信息面
req('GET', '/v1/projects/%s' % PROJECT_REF, None, 'proj-detail')
# 4. database hosts / 连接端点
req('GET', '/v1/projects/%s/database/hosts' % PROJECT_REF, None, 'db-hosts')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb44_final.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('ttl=%ds' % (1788510807 - int(time.time())))
print('\n'.join(out)[:8000])
