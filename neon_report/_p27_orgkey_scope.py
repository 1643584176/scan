# -*- coding: utf-8 -*-
"""org-scoped API key scope 隔离实测:
假设: org key + project_id(声称 only this project) 的 scope 是否拦住管理面/个人面/其他 org 操作
流程: 建 org key(带 project_id=A) -> key 跑矩阵(400 vs 403/404 区分授权层) -> revoke 清理
"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ORG = 'org-flat-dawn-91601224'
PID = 'orange-sun-90493739'

def ctl_req(method, path, body=None, key=None, with_cookie=True):
    try:
        fresh = {}
        csrf = None
        if with_cookie:
            conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
            conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
            r = conn.getresponse(); r.read()
            for sc in r.headers.get_all('Set-Cookie') or []:
                m = re.match(r'([^=]+)=([^;]*)', sc)
                if m: fresh[m.group(1)] = m.group(2)
            conn.close()
            conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
            conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
            r2 = conn2.getresponse(); txt = r2.read().decode('utf-8', 'replace'); conn2.close()
            m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
            csrf = html.unescape(m.group(1)) if m else None
        parts = []
        if with_cookie:
            for c in cookie_str().split(';'):
                c = c.strip()
                if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
                    parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
                else:
                    parts.append(c)
        conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
        hdrs = {'User-Agent': 'Mozilla/5.0'}
        if with_cookie:
            hdrs['Cookie'] = '; '.join(parts)
        if key:
            hdrs['Authorization'] = 'Bearer ' + key
        hdrs.update(HEADERS_TEST)
        if body is not None:
            hdrs['Content-Type'] = 'application/json'
        if csrf:
            hdrs['X-CSRF-Token'] = csrf
        conn3.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
        r3 = conn3.getresponse()
        out = r3.read().decode('utf-8', 'ignore')
        conn3.close()
        return r3.status, out
    except Exception as e:
        return -1, 'EXC %s' % e

# ---- 1. 建 org-scoped key ----
print('=== 1. create org key (project-scoped) ===', flush=True)
st, raw = ctl_req('POST', API_BASE + '/organizations/%s/api_keys' % ORG,
                  {'key_name': 'sctest1', 'project_id': PID})
print('-> %d %s' % (st, raw[:400].replace('\n', ' ')), flush=True)
key = None
try:
    d = json.loads(raw)
    key = d.get('key') or (d.get('api_key') or {}).get('key')
except Exception:
    pass
if not key:
    # 试 body 变体
    for body in [{'key_name': 'sctest1'}, {'name': 'sctest1', 'project_id': PID}, {'key_name': 'sctest1', 'scope': {'project_id': PID}}]:
        st2, raw2 = ctl_req('POST', API_BASE + '/organizations/%s/api_keys' % ORG, body)
        print('  body %s -> %d %s' % (json.dumps(body)[:60], st2, raw2[:250].replace('\n', ' ')), flush=True)
        try:
            d2 = json.loads(raw2)
            key = d2.get('key') or (d2.get('api_key') or {}).get('key')
            if key:
                break
        except Exception:
            pass
        time.sleep(0.3)
if not key:
    print('NO KEY created, abort', flush=True)
    raise SystemExit
print('KEY:', key[:24] + '...', flush=True)

# ---- 2. key 权限矩阵 ----
print('\n=== 2. org key scope 矩阵 ===', flush=True)
tests = [
    ('GET', API_BASE + '/projects?limit=5', None, 'project list (个人面? 返回范围?)'),
    ('GET', API_BASE + '/projects/' + PID, None, 'project A (应 200)'),
    ('GET', API_BASE + '/projects/' + PID + '/branches', None, 'branches of A'),
    ('GET', API_BASE + '/organizations/' + ORG, None, 'org 详情 (管理面?)'),
    ('GET', API_BASE + '/organizations/' + ORG + '/members', None, 'org members (管理面?)'),
    ('GET', API_BASE + '/organizations/' + ORG + '/api_keys', None, 'org api_keys list (管理面?)'),
    ('GET', API_BASE + '/users/me', None, 'current user (个人面?)'),
    ('GET', API_BASE + '/users/me/organizations', None, 'my orgs (个人面?)'),
    ('GET', API_BASE + '/api_keys', None, 'personal api keys (个人面?)'),
    ('GET', API_BASE + '/organizations/' + ORG + '/billing/spending_limit', None, 'billing (管理面?)'),
    ('POST', API_BASE + '/projects/' + PID + '/transfer_requests', {'ttl_seconds': -1}, 'project 写面 ttl=-1 (400=过授权)'),
    ('POST', API_BASE + '/projects/' + PID + '/branches', {}, 'project 写面 create branch 空体 (400/422=过授权)'),
    ('POST', API_BASE + '/organizations/' + ORG + '/projects/transfer', {}, 'org 写面 transfer 空体 (400=过授权)'),
    ('GET', API_BASE + '/projects/does-not-exist-xyz', None, '不存在 project (404 vs 403)'),
]
for m, p, b, note in tests:
    st, raw = ctl_req(m, p, body=b, key=key, with_cookie=False)
    print('[%s] -> %d | %s | %s' % (note, st, p.replace(API_BASE, ''), raw[:160].replace('\n', ' ')), flush=True)
    time.sleep(0.25)

# ---- 3. 清理 revoke ----
print('\n=== 3. cleanup ===', flush=True)
st, raw = ctl_req('GET', API_BASE + '/organizations/' + ORG + '/api_keys')
kid = None
try:
    for k in json.loads(raw).get('api_keys', []):
        if k.get('name') == 'sctest1':
            kid = k.get('id')
except Exception:
    pass
if kid:
    st2, raw2 = ctl_req('DELETE', API_BASE + '/organizations/' + ORG + '/api_keys/' + kid)
    print('revoke -> %d %s' % (st2, raw2[:120].replace('\n', ' ')), flush=True)
else:
    print('key not found for cleanup, manual: id in raw:', raw[:300], flush=True)
