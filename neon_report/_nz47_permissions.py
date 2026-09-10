# -*- coding: utf-8 -*-
"""T2: permissions grant 校验逻辑 (grant 外部/不存在邮箱 -> 响应差异; 列表; revoke 清理) 5 req"""
import http.client, ssl, json, time, sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
ctx = ssl.create_default_context()
R = uuid.uuid4().hex[:8]

def req(tag, path, body=None, method=None):
    m = method or ('POST' if body is not None else 'GET')
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(m, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            print('== %-34s -> %d  %s' % (tag, r.status, raw[:400].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

# 1) grant 给不存在域邮箱
st, raw = req('grant 不存在邮箱', '/projects/%s/permissions' % PA,
              {'email': 'sbx_share_%s@example.com' % R})
pid = None
try:
    pid = json.loads(raw).get('id')
    print('   permission_id =', pid)
except Exception:
    pass

# 2) grant 给非法格式
req('grant 非法email', '/projects/%s/permissions' % PA, {'email': 'not-an-email'})

# 3) grant 给自己(org owner 已在 org)
req('grant 自己邮箱', '/projects/%s/permissions' % PA, {'email': 'libobo1229@gmail.com'})

# 4) 列表确认
st2, raw2 = req('列表', '/projects/%s/permissions' % PA)

# 5) revoke 清理 (若存在)
if pid:
    req('revoke', '/projects/%s/permissions/%s' % (PA, pid), method='DELETE')
    req('revoke 后列表', '/projects/%s/permissions' % PA)
