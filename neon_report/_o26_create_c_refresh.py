# -*- coding: utf-8 -*-
"""建 project C + storage 确认(带 keycloak refresh 自动续期)"""
import http.client, ssl, json, re, html, os, sys, time, urllib.parse

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def get_cookie(force_refresh=False):
    """返回可用 cookie;失败/force 时用 refresh_token 换新"""
    if not force_refresh:
        # 试一次
        try:
            conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
            conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
            r = conn.getresponse()
            st = r.status
            r.read()
            conn.close()
            if st == 200:
                return cookie_str()
        except Exception:
            pass
    # refresh:从 cookie 提取 keycloak_token JSON 的 RefreshToken
    raw_cookie = cookie_str()
    m = re.search(r'keycloak_token=([^;]+)', raw_cookie)
    if not m:
        print('no keycloak_token in cookie'); raise SystemExit(1)
    kc_json = json.loads(urllib.parse.unquote(m.group(1)))
    refresh = kc_json['RefreshToken']
    # POST token 端点
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    body = urllib.parse.urlencode({
        'grant_type': 'refresh_token', 'client_id': 'neon-console',
        'refresh_token': refresh,
    })
    conn.request('POST', '/realms/staging-realm/protocol/openid-connect/token', body=body,
                 headers={'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0'})
    r = conn.getresponse()
    raw = r.read().decode('utf-8', 'replace')
    conn.close()
    print('refresh -> %d %s' % (r.status, raw[:150]), flush=True)
    if r.status != 200:
        print('refresh failed'); raise SystemExit(1)
    d = json.loads(raw)
    new_kc = json.dumps({'AccessToken': d['access_token'], 'RefreshToken': d.get('refresh_token', refresh)})
    new_cookie = re.sub(r'keycloak_token=[^;]+', 'keycloak_token=' + urllib.parse.quote(new_kc), raw_cookie)
    # 验证
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': new_cookie})
    r = conn.getresponse()
    st = r.status
    r.read()
    conn.close()
    print('verify GET / ->', st, flush=True)
    if st != 200:
        print('new cookie still fails'); raise SystemExit(1)
    return new_cookie

CK = get_cookie()
print('cookie ok, len:', len(CK), flush=True)

def csrf_cookie(cookie):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m2 = re.match(r'([^=]+)=([^;]*)', sc)
        if m2:
            fresh[m2.group(1)] = m2.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
    r2 = conn2.getresponse()
    txt = r2.read().decode('utf-8', 'replace')
    conn2.close()
    m2 = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m2.group(1)) if m2 else None
    parts = []
    for c in cookie.split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    return '; '.join(parts), csrf

def ctl(method, path, body=None):
    ck, csrf = csrf_cookie(CK)
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=90)
    hdrs = {'Cookie': ck, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf,
            'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
    r = conn.getresponse()
    raw = r.read().decode('utf-8', 'ignore')
    conn.close()
    return r.status, raw

st, raw = ctl('POST', '/projects', {'project': {'name': 'sec-cross-store-' + str(int(time.time()))[-6:],
                                                 'region_id': 'aws-us-east-2', 'pg_version': 17},
                                                'org_id': 'org-flat-dawn-91601224'})
print('create -> %d %s' % (st, raw[:600].replace('\n', ' ')), flush=True)
d = json.loads(raw)
pid = d['project']['id']
bids = [b['id'] for b in d.get('branches', [])]
print('PID:', pid, 'BID:', bids, flush=True)
import io as _io
_io.open('_ctx_c.json', 'w', encoding='utf-8').write(json.dumps({'pid': pid, 'bid': bids[0] if bids else ''}))
time.sleep(6)
for path in ['/projects/%s/branches/%s/storage' % (pid, bids[0]),
             '/projects/%s/branches/%s/ai_gateway' % (pid, bids[0])]:
    st, raw = ctl('GET', path)
    print('GET %s -> %d %s' % (path.split('/')[-1], st, raw[:400].replace('\n', ' ')), flush=True)
