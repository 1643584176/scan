# -*- coding: utf-8 -*-
"""transfer 攻击前状态盘点:
1. na2/na1 视角: A 项目归属(personal? org?)+项目列表
2. org 列表 + 成员
3. 试探 GET /projects/{pid}/transfer_requests 是否存在(pending 泄露面)
4. na2 建 transfer request(ttl=120) 观察响应 + claim link 形态
"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def ctl_req(cookie, method, path, body=None, ctype='application/json', raw_body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
    r2 = conn2.getresponse()
    txt = r2.read().decode('utf-8', 'replace')
    conn2.close()
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie.split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
    hdrs.update(HEADERS_TEST)
    if ctype:
        hdrs['Content-Type'] = ctype
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn3.request(method, path, body=data, headers=hdrs)
    r3 = conn3.getresponse()
    out = r3.read().decode('utf-8', 'ignore')
    conn3.close()
    return r3.status, out

# na2 视角
ck = cookie_str()
st, raw = ctl_req(ck, 'GET', API_BASE + '/projects?limit=50')
print('[na2] GET /projects -> %d' % st, flush=True)
try:
    projs = json.loads(raw).get('projects', [])
    for p in projs:
        print('  pid=%s name=%s owner=%s org=%s branch=%s' % (
            p.get('id'), p.get('name'), (p.get('owner') or {}).get('email') if p.get('owner') else None,
            (p.get('org_id') or (p.get('owner') or {}).get('org_id') if p.get('owner') else None),
            len(p.get('branch_ids', []))), flush=True)
except Exception as e:
    print('  parse err', e, raw[:300], flush=True)

st, raw = ctl_req(ck, 'GET', API_BASE + '/organizations?limit=50')
print('\n[na2] GET /organizations -> %d' % st, flush=True)
print(' ', raw[:600], flush=True)

# A 项目详情(找归属字段)
st, raw = ctl_req(ck, 'GET', API_BASE + '/projects/orange-sun-90493739')
print('\n[na2] GET /projects/orange-sun-90493739 -> %d' % st, flush=True)
print(' ', raw[:900], flush=True)

# GET pending transfer requests(探测端点)
st, raw = ctl_req(ck, 'GET', API_BASE + '/projects/orange-sun-90493739/transfer_requests')
print('\n[na2] GET transfer_requests -> %d %s' % (st, raw[:300]), flush=True)

# POST create transfer request(ttl 短, 自清理)
st, raw = ctl_req(ck, 'POST', API_BASE + '/projects/orange-sun-90493739/transfer_requests',
                  {'ttl_seconds': 120})
print('\n[na2] POST create transfer -> %d %s' % (st, raw[:500]), flush=True)
