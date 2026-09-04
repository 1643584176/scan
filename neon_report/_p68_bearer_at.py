# -*- coding: utf-8 -*-
"""keycloak_token 解析 -> Bearer 测 /api/v2/database_instances"""
import http.client, ssl, json, sys, os, urllib.parse, re, base64

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import COOKIE_RAW, API_HOST

def base64_url_decode(s):
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

# 解析 keycloak_token cookie
m = re.search(r'keycloak_token=([^;]+)', COOKIE_RAW)
raw = urllib.parse.unquote(m.group(1))
kc = json.loads(raw)
AT = kc['AccessToken']
print('AccessToken len:', len(AT), flush=True)
# 看 payload 里有什么
p = AT.split('.')[1]
p += '=' * (-len(p) % 4)
pl = json.loads(base64_url_decode(p))
print('claims:', json.dumps(pl, indent=1)[:800], flush=True)

def req(path, bearer=None, cookie=False):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        if bearer:
            h['Authorization'] = 'Bearer ' + bearer
        if cookie:
            h['Cookie'] = COOKIE_RAW
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw[:400].replace('\n', ' ')
    except Exception as e:
        return -1, 'EXC %s' % e

print('=== Bearer keycloak AT ===', flush=True)
for p in ['/api/v2/database_instances', '/api/v2/projects', '/api/v2/users/me', '/api/v2/organizations']:
    st, body = req(p, bearer=AT)
    print('%-40s %s %s' % (p, st, body[:200]), flush=True)
