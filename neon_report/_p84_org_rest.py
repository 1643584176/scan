# -*- coding: utf-8 -*-
"""1. org/users 只读面补全 + 2. bat passwordless/oauth token 方法体逆向"""
import re, os, sys, http.client, ssl, json, time

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
i_bat = src.find('class bat extends yat')
i_kde = src.find('const Kde')
seg = src[i_bat:i_kde]

out = []
for kw in ['passwordless', 'OAuthToken', 'oauth_token', 'session/oauth', 'runProjectSqlQuery']:
    # 整个 index 找定义(方法体含 path:)
    for mm in re.finditer(re.escape(kw), seg):
        i = mm.start()
        ctx2 = seg[max(0, i - 150):i + 350].replace('\n', ' ')
        if 'path:' in ctx2 or 'this.request' in ctx2:
            out.append('KW %s @bat+%d: %s' % (kw, i, ctx2[:460]))
            break
    else:
        out.append('KW %s: no def found in bat seg' % kw)
# oauth token path 全局搜(可能不在 bat 段)
for kw in ['grant-type:session', 'urn:databricks', '!pgsql']:
    idxs = [mm.start() for mm in re.finditer(re.escape(kw), src)]
    out.append('GLOBAL %s -> %d' % (kw, len(idxs)))
    for i in idxs[:4]:
        out.append('  @%d: %s' % (i, src[max(0, i - 200):i + 250].replace('\n', ' ')[:420]))
open(os.path.join(here, '_p84_rev.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)

# HTTP 部分
ctx = ssl.create_default_context()
sys.path.insert(0, here)
from _neon_creds_prod import COOKIE_RAW, API_HOST
m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)
O = 'org-calm-sound-68506202'
PID = 'jolly-term-94460232'
BID = 'br-orange-flower-a57knkws'
EP = 'ep-late-boat-a5cdpoh2'

def req(path, csrf=True, method='GET', body=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'application/json', 'Cookie': COOKIE_RAW}
        if csrf:
            h['X-CSRF-Token'] = CSRF
        conn.request(method, path, headers=h, body=body)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw
    except Exception as e:
        return -1, 'EXC %s' % e

print('=== org/users 只读面 ===', flush=True)
tests = [
    ('GET', '/api/v2/organizations/%s' % O, None),
    ('GET', '/api/v2/organizations/%s/members?limit=20' % O, None),
    ('GET', '/api/v2/organizations/%s/invitations' % O, None),
    ('GET', '/api/v2/organizations/%s/guests' % O, None),
    ('GET', '/api/v2/organizations/%s/domains' % O, None),
    ('GET', '/api/v2/organizations/%s/sso' % O, None),
    ('GET', '/api/v2/organizations/%s/sso/enforcement' % O, None),
    ('GET', '/api/v2/organizations/%s/api_keys' % O, None),
    ('GET', '/api/v2/users/me/auth' % (), None),
    ('GET', '/api/v2/users/me/refcode' % (), None),
    ('GET', '/api/v2/users/me/consumption' % (), None),
]
for method, p, body in tests:
    st, b = req(p, True, method, body)
    print('%-72s %s %s' % (p, st, b[:500].replace('\n', ' ')), flush=True)
    time.sleep(0.25)
