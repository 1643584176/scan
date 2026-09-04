# -*- coding: utf-8 -*-
"""假设A: 注册用户拿 authenticated 角色 + pg_tle 探针 + auth 配置确认"""
import http.client, ssl, json, time, os, sys, random, string
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _supabase_creds import BEARER_JWT, VDP_HEADERS, UA, API_HOST, PROJECT_REF

ctx = ssl.create_default_context()
out = []
def req(method, path, body=None, tag='', host=API_HOST, bearer=None):
    body_j = json.dumps(body) if body is not None else None
    c = http.client.HTTPSConnection(host, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json"}
    if bearer is not None:
        h["Authorization"] = "Bearer " + bearer
    if body_j:
        h["Content-Type"] = "application/json"
    h.update(VDP_HEADERS)
    t0 = time.time()
    try:
        c.request(method, path, headers=h, body=body_j)
        r = c.getresponse()
        b = r.read(6000).decode('utf-8', errors='replace')
        out.append('### [%s] %s %s (%.1fs)\n%s | %s' % (tag, method, path, time.time() - t0, r.status, b[:3000]))
        c.close()
        return r.status, b
    except Exception as e:
        out.append('### [%s] %s %s ERR %s' % (tag, method, path, e))
        return 0, str(e)

def q(sql, tag):
    body = json.dumps({"query": sql})
    c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json",
         "Authorization": "Bearer " + BEARER_JWT}
    h.update(VDP_HEADERS)
    try:
        c.request('POST', '/v1/projects/%s/database/query' % PROJECT_REF, headers=h, body=body)
        r = c.getresponse()
        b = r.read(4000).decode('utf-8', errors='replace')
        out.append('### [%s]\n%s | %s' % (tag, r.status, b[:2000]))
        c.close()
    except Exception as e:
        out.append('### [%s] ERR %s' % (tag, e))

# 1. auth 配置 (email confirm 状态)
req('GET', '/v1/projects/%s/config/auth' % PROJECT_REF, None, 'cfg-auth')
# 2. GoTrue signup 随机邮箱 (auth host)
suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
TEST_EMAIL = 'sbx_au_%s@example.com' % suffix
st, b = req('POST', '/auth/v1/signup', {"email": TEST_EMAIL, "password": "Sbxtest123!"},
            'signup', host='%s.supabase.co' % PROJECT_REF, bearer=None)
# 3. pg_tle 探针
q("select extversion from pg_extension where extname='pg_tle';", 'tle-ext')
q("select proname from pg_proc where pronamespace='pgtle'::regnamespace limit 20;", 'tle-funcs')
q("select name, default_version from pg_available_extensions where name in ('pg_tle','pgsodium','supabase_vault','http','pgjwt','pg_graphql','vector','hypopg');", 'avail-ext')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sb62_signup.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
