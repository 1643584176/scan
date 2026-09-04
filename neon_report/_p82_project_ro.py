# -*- coding: utf-8 -*-
"""有项目了: jolly-term-94460232. project 级只读探测(全 GET 零写):
1. project 详情/branches/endpoints 拿资源 id
2. console 私有 project 级端点批量只读
3. ai_gateway 控制面(models/resolve_identity 带 pid)
"""
import http.client, ssl, re, os, sys, json, time

ctx = ssl.create_default_context()
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from _neon_creds_prod import COOKIE_RAW, API_HOST

m = re.search(r'_gorilla_csrf=([^;]+)', COOKIE_RAW)
CSRF = m.group(1)
O = 'org-calm-sound-68506202'
PID = 'jolly-term-94460232'

def req(path, csrf=None):
    try:
        conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
             'Accept': 'application/json', 'Cookie': COOKIE_RAW}
        if csrf:
            h['X-CSRF-Token'] = csrf
        conn.request('GET', path, headers=h)
        r = conn.getresponse()
        raw = r.read().decode('utf-8', 'ignore')
        conn.close()
        return r.status, raw
    except Exception as e:
        return -1, 'EXC %s' % e

def show(tag, p, csrf=True):
    st, b = req(p, CSRF if csrf else None)
    print('%s %-80s %s %s' % ('---', p, st, b[:600].replace('\n', ' ')), flush=True)
    time.sleep(0.25)
    return st, b

# 1. 资源枚举
st, b = show('E', '/api/v2/projects/%s?org_id=%s' % (PID, O))
try:
    d = json.loads(b)
    print('project:', d.get('project', {}).get('id'), d.get('project', {}).get('name'), flush=True)
except Exception:
    pass
st, b = show('E', '/api/v2/projects/%s/branches?org_id=%s&limit=10' % (PID, O))
BID = None
try:
    d = json.loads(b)
    brs = d.get('branches', [])
    if brs:
        BID = brs[0]['id']
        print('branches:', [(x['id'], x['name']) for x in brs], flush=True)
except Exception:
    pass
st, b = show('E', '/api/v2/projects/%s/endpoints?org_id=%s' % (PID, O))

if not BID:
    print('NO BRANCH, exit', flush=True)
    sys.exit(0)

# 2. console 私有 project 级只读端点
priv = [
    '/api/v2/projects/%s/platform-served?org_id=%s',
    '/api/v2/projects/%s/consumption?org_id=%s',
    '/api/v2/projects/%s/limits?org_id=%s',
    '/api/v2/projects/%s/permissions?org_id=%s',
    '/api/v2/projects/%s/members?org_id=%s',
    '/api/v2/projects/%s/operations?org_id=%s&limit=5',
    '/api/v2/projects/%s/running_operations?org_id=%s',
    '/api/v2/projects/%s/snapshots?org_id=%s&limit=5',
    '/api/v2/projects/%s/notifications?org_id=%s',
    '/api/v2/projects/%s/advisors?org_id=%s',
    '/api/v2/projects/%s/saved_queries?org_id=%s',
    '/api/v2/projects/%s/query/history?org_id=%s&limit=5',
    '/api/v2/projects/%s/branches/count?org_id=%s',
    '/api/v2/projects/%s/branch_anonymized?org_id=%s',
    '/api/v2/projects/%s/available_preload_libraries?org_id=%s',
    '/api/v2/projects/%s/integrations/monitoring?org_id=%s',
    '/api/v2/projects/%s/jwks?org_id=%s',
    '/api/v2/projects/%s/usage-status?org_id=%s',
]
for p in priv:
    show('P', p % (PID, O))

# branch 级私有
bpriv = [
    '/api/v2/projects/%s/branches/%s/consumption?org_id=%s',
    '/api/v2/projects/%s/branches/%s/storage?org_id=%s',
    '/api/v2/projects/%s/branches/%s/backup_schedule?org_id=%s',
    '/api/v2/projects/%s/branches/%s/anonymized_status?org_id=%s',
    '/api/v2/projects/%s/branches/%s/ai_gateway?org_id=%s',
    '/api/v2/projects/%s/branches/%s/logs/fields?org_id=%s',
    '/api/v2/projects/%s/branches/%s/masking_rules?org_id=%s',
    '/api/v2/projects/%s/branches/%s/buckets?org_id=%s',
    '/api/v2/projects/%s/branches/%s/data-api/list?org_id=%s',
]
for p in bpriv:
    show('B', p % (PID, BID, O))

# 3. ai_gateway 账号级
for p in ['/api/v2/ai_gateway/models?project_id=%s&org_id=%s' % (PID, O),
          '/api/v2/ai_gateway/resolve_identity?project_id=%s' % PID]:
    show('A', p)
