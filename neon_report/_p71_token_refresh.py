# -*- coding: utf-8 -*-
"""keycloak refresh_token 换新 AccessToken -> 更新 COOKIE_RAW -> 验证 /api/v2"""
import http.client, ssl, json, sys, os, urllib.parse, re, base64

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import COOKIE_RAW, API_HOST

def b64d(s):
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

# 解析现有 keycloak_token
m = re.search(r'keycloak_token=([^;]+)', COOKIE_RAW)
kc = json.loads(urllib.parse.unquote(m.group(1)))
RT = kc['RefreshToken']

# 调 keycloak token endpoint refresh
conn = http.client.HTTPSConnection('console.neon.tech', context=ctx, timeout=30)
body = urllib.parse.urlencode({
    'grant_type': 'refresh_token',
    'refresh_token': RT,
    'client_id': 'neon-console',
})
conn.request('POST', '/realms/prod-realm/protocol/openid-connect/token', body=body,
             headers={'Content-Type': 'application/x-www-form-urlencoded',
                      'User-Agent': 'Mozilla/5.0'})
r = conn.getresponse()
raw = r.read().decode('utf-8', 'ignore')
conn.close()
print('refresh status:', r.status, flush=True)
if r.status != 200:
    print(raw[:500], flush=True)
    raise SystemExit
tok = json.loads(raw)
new_at = tok.get('access_token', '')
new_rt = tok.get('refresh_token', RT)
print('new AT len:', len(new_at), 'expires_in:', tok.get('expires_in'), flush=True)

# 组新 keycloak_token cookie 值
new_kc = urllib.parse.quote(json.dumps({'AccessToken': new_at, 'RefreshToken': new_rt}))
new_cookie = re.sub(r'keycloak_token=[^;]+', 'keycloak_token=' + new_kc, COOKIE_RAW)
print('new cookie len:', len(new_cookie), flush=True)

# 验证
def req(path):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=20)
        conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0',
                                           'Accept': 'application/json', 'Cookie': new_cookie})
        r = conn.getresponse()
        out = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, out[:400].replace('\n', ' ')
    except Exception as e:
        return -1, 'EXC %s' % e

for p in ['/api/v2/users/me', '/api/v2/projects?limit=5', '/api/v2/database_instances']:
    st, body = req(p)
    print('%-40s %s %s' % (p, st, body[:300]), flush=True)

# 保存新 cookie 到 creds 文件
creds_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_neon_creds_prod.py')
s = open(creds_p, encoding='utf-8').read()
s = re.sub(r'COOKIE_RAW = """[\s\S]*?"""', 'COOKIE_RAW = """' + new_cookie + '"""', s, count=1)
open(creds_p, 'w', encoding='utf-8').write(s)
print('creds updated', flush=True)
