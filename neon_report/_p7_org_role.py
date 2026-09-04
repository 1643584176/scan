# -*- coding: utf-8 -*-
"""查: 1. org-flat-dawn members 角色(na2 owner/member?)
2. POST /organizations 建 org 端点存在性
3. DELETE transfer_request 端点存在性"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def ctl_req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r = conn.getresponse()
    r.read()
    fresh = {}
    for sc in r.headers.get_all('Set-Cookie') or []:
        m = re.match(r'([^=]+)=([^;]*)', sc)
        if m:
            fresh[m.group(1)] = m.group(2)
    conn.close()
    conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    conn2.request('GET', '/', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str()})
    r2 = conn2.getresponse()
    txt = r2.read().decode('utf-8', 'replace')
    conn2.close()
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', txt)
    csrf = html.unescape(m.group(1)) if m else None
    parts = []
    for c in cookie_str().split(';'):
        c = c.strip()
        if c.startswith('_gorilla_csrf=') and '_gorilla_csrf' in fresh:
            parts.append('_gorilla_csrf=' + fresh['_gorilla_csrf'])
        else:
            parts.append(c)
    conn3 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
    hdrs = {'Cookie': '; '.join(parts), 'User-Agent': 'Mozilla/5.0'}
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

# 1. org members
st, raw = ctl_req('GET', API_BASE + '/organizations/org-flat-dawn-91601224/members')
print('[1] org members -> %d' % st, flush=True)
try:
    for mem in json.loads(raw).get('members', []):
        print('  role=%s email=%s uid=%s' % (mem.get('role'), (mem.get('user') or {}).get('email'),
                                             mem.get('user_id') or (mem.get('user') or {}).get('id')), flush=True)
except Exception as e:
    print('  err', e, raw[:400], flush=True)

# 2. org 详情(看 owner/role 字段)
st, raw = ctl_req('GET', API_BASE + '/organizations/org-flat-dawn-91601224')
print('\n[2] org detail -> %d' % st, flush=True)
print(' ', raw[:600], flush=True)

# 3. POST /organizations 建 org 端点
st, raw = ctl_req('POST', API_BASE + '/organizations', {'name': 'sec-probe-org-x'})
print('\n[3] POST /organizations -> %d %s' % (st, raw[:300]), flush=True)

# 4. DELETE transfer request(清理 8be8ff65 残留)
st, raw = ctl_req('DELETE', API_BASE + '/projects/orange-sun-90493739/transfer_requests/8be8ff65-4da2-488c-b6e4-2c08b80d2ceb')
print('\n[4] DELETE transfer_request -> %d %s' % (st, raw[:300]), flush=True)
