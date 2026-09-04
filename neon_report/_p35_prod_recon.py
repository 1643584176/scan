# -*- coding: utf-8 -*-
"""production 只读侦察:
1. 会话有效性: GET /users/me + GET /projects (看 prod 账号资源)
2. observability-settings(自己项目, 200/404 分层)
3. configs 列表端点盲试(只读)
4. 注意: 全部 GET, 零写操作
"""
import http.client, ssl, json, re, html, sys, os, time

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_prod import API_HOST, API_BASE, HEADERS_TEST, cookie_str

def ctl_req(method, path, body=None, with_cookie=True):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
        conn.request(method, path, headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie_str(), 'Accept': 'application/json'})
        r = conn.getresponse()
        out = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, out
    except Exception as e:
        return -1, 'EXC %s' % e

print('=== 1. 会话 + 资源 ===', flush=True)
for p in ['/users/me', '/projects?limit=10', '/users/me/organizations']:
    st, raw = ctl_req('GET', API_BASE + p)
    print('[%s] -> %d %s' % (p, st, raw[:600].replace('\n', ' ')), flush=True)
    time.sleep(0.3)

print('\n=== 2. observability-settings(自己项目) ===', flush=True)
# 从 projects 响应拿 pid
st, raw = ctl_req('GET', API_BASE + '/projects?limit=10')
pids = []
try:
    d = json.loads(raw)
    pids = [pr['id'] for pr in d.get('projects', [])]
except Exception as e:
    print('parse err', e, flush=True)
print('my projects:', pids, flush=True)
for pid in pids[:3]:
    st, raw = ctl_req('GET', '/ajax-api/2.0/postgres/projects/%s/observability-settings' % pid)
    print('[%s] -> %d %s' % (pid, st, raw[:400].replace('\n', ' ')), flush=True)
    time.sleep(0.3)
# 不存在的项目(404 vs 200 分层参考)
st, raw = ctl_req('GET', '/ajax-api/2.0/postgres/projects/does-not-exist-xyz/observability-settings')
print('[noexist] -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)

print('\n=== 3. configs 列表端点盲试(只读 GET) ===', flush=True)
cands = ['/ajax-api/2.0/postgres/observability/configurations',
         '/ajax-api/2.0/observability/configurations',
         '/ajax-api/2.0/observability/configs',
         '/ajax-api/2.0/postgres/configurations',
         '/ajax-api/2.0/configurations',
         '/ajax-api/2.0/postgres/observability',
         '/ajax-api/2.0/observability',
         '/ajax-api/2.0/postgres/projects/%s/observability-configurations' % (pids[0] if pids else 'x'),
         '/ajax-api/2.0/postgres/projects/%s/configurations' % (pids[0] if pids else 'x')]
for p in cands:
    st, raw = ctl_req('GET', p)
    print('[%s] -> %d %s' % (p.replace('/ajax-api', 'ajax-api'), st, raw[:200].replace('\n', ' ')), flush=True)
    time.sleep(0.2)
