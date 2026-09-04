# -*- coding: utf-8 -*-
"""跨租户 JWT 复用测试准备: 用 API key 创建第二个项目
流程: 建项目 -> 等 active -> 拿分支/连接信息 -> 记录 _ctx_b.json"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
API_HOST = 'console-stage.neon.build'
API_BASE = '/api/v2'

keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
if isinstance(keyj, dict):
    KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
else:
    KEY = keyj
print('key 类型:', 'dict' if isinstance(keyj, dict) else type(keyj).__name__)

def req(method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    raw = r.read()
    st = r.status
    conn.close()
    return st, raw

# 1. API key 权限自检: 项目列表(org 从 _ctx.json)
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
ORG = ctxj.get('org', '')
st, raw = req('GET', API_BASE + '/projects?org_id=' + ORG)
print('\n[1] GET /projects -> %d %s' % (st, raw.decode(errors='replace')[:300]))

# 2. 创建第二个项目(名字带时间戳, body 需嵌套 project)
name = 'k-jwt-x%d' % int(time.time() % 100000)
body = {'project': {'name': name, 'region_id': 'aws-us-east-2', 'org_id': ORG}}
st, raw = req('POST', API_BASE + '/projects', body)
print('\n[2] POST /projects %s -> %d %s' % (name, st, raw.decode(errors='replace')[:400]))
try:
    pj = json.loads(raw)
    pid2 = pj.get('project', {}).get('id') or pj.get('id')
except Exception:
    pid2 = None
if not pid2:
    print('创建失败, 尝试其他 body 变体')
    for b2 in ({'project': {'name': name, 'region_id': 'aws-us-east-2'}},
               {'project': {'name': name, 'region_id': 'us-east-2'}},
               {'name': name}):
        st, raw = req('POST', API_BASE + '/projects', b2)
        print('  variant %s -> %d %s' % (list(b2.keys()), st, raw.decode(errors='replace')[:200]))
        try:
            pj = json.loads(raw)
            pid2 = pj.get('project', {}).get('id') or pj.get('id')
        except Exception:
            pid2 = None
        if pid2:
            break
print('project id:', pid2)
if not pid2:
    sys.exit(1)
time.sleep(2)

# 3. 等项目 active + 拿分支
for i in range(20):
    st, raw = req('GET', API_BASE + '/projects/' + pid2)
    try:
        pj = json.loads(raw)
        pr = pj.get('project', pj)
        state = pr.get('status') or pr.get('state') or pr.get('platform_state') or 'unknown'
        if state in ('active', 'ready', 'Active'):
            break
    except Exception:
        pass
    print('  等待项目就绪 %d (%s)...' % (i, state if 'state' in dir() else ''))
    time.sleep(5)
print('项目状态:', state)

# 4. 分支列表
st, raw = req('GET', API_BASE + '/projects/%s/branches' % pid2)
print('\n[4] branches -> %d %s' % (st, raw.decode(errors='replace')[:300]))
bid2 = None
try:
    bs = json.loads(raw)
    brs = bs.get('branches', [])
    for b in brs:
        if b.get('primary'):
            bid2 = b['id']
    if not bid2 and brs:
        bid2 = brs[0]['id']
except Exception:
    pass
print('branch id:', bid2)

# 5. 连接串(拿 owner 密码 + 端点)
st, raw = req('POST', API_BASE + '/projects/%s/connection-uris' % pid2,
              {'database_name': 'neondb', 'role_name': 'neondb_owner', 'branch_id': bid2})
print('\n[5] connection-uris -> %d %s' % (st, raw.decode(errors='replace')[:500]))
conn_info = {}
try:
    ci = json.loads(raw)
    uri = ci.get('connection_uris', [{}])[0].get('connection_uri', '')
    if not uri and isinstance(ci, dict):
        uri = ci.get('connection_uri', '')
    conn_info['uri'] = uri
except Exception:
    pass

# 6. 落盘
out = {'pid2': pid2, 'bid2': bid2, 'name': name, 'conn': conn_info}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx_b.json'), 'w') as f:
    json.dump(out, f, indent=1)
print('\n记录:', json.dumps(out)[:300])
