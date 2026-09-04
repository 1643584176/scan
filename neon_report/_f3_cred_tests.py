# -*- coding: utf-8 -*-
"""Credentials 面测试:
A. principal_type=function(平台内部类型)注入
B. scopes 注入 telemetry:write(平台内部 scope)
C. 未知 scope 校验
D. 子分支 credential 继承语义
全部自建 kc1/kc2...,结束清理。"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'

def req(method, path, body=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=25)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
    return st, raw

def show(tag, r):
    st, raw = r
    print('[%s] -> %d | %s' % (tag, st, raw.decode(errors='replace')[:400]))

# A. principal_type=function
show('A function-pt', req('POST', '/projects/%s/branches/%s/credentials' % (P, B),
                          {'name': 'kcA', 'scopes': ['storage:read'], 'principal_type': 'function'}))

# B. scopes 注入 telemetry:write(user pt)
show('B telemetry-w', req('POST', '/projects/%s/branches/%s/credentials' % (P, B),
                          {'name': 'kcB', 'scopes': ['storage:read', 'telemetry:write'], 'principal_type': 'user'}))

# C. 未知 scope
show('C unknown-scope', req('POST', '/projects/%s/branches/%s/credentials' % (P, B),
                            {'name': 'kcC', 'scopes': ['storage:read', 'admin:*'], 'principal_type': 'user'}))

# D. 正常 create 基线 + 子分支继承
show('D1 create kcD', req('POST', '/projects/%s/branches/%s/credentials' % (P, B),
                          {'name': 'kcD', 'scopes': ['storage:read'], 'principal_type': 'user'}))
st, raw = req('POST', '/projects/%s/branches' % (P,), {'name': 'k-br-cred', 'parent_id': B})
show('D2 create child', (st, raw))
CB = None
try:
    CB = json.loads(raw)['branch']['id']
except Exception:
    try:
        CB = json.loads(raw)['id']
    except Exception:
        pass
print('child branch:', CB)
if CB:
    time.sleep(2)
    show('D3 child list creds(inherit?)', req('GET', '/projects/%s/branches/%s/credentials' % (P, CB)))

# 清理:kcD + 子分支
st, raw = req('GET', '/projects/%s/branches/%s/credentials' % (P, B))
try:
    creds = json.loads(raw).get('credentials', [])
    for c_ in creds:
        if c_.get('name', '').startswith('kc') and c_.get('principal_type') == 'user':
            show('clean %s' % c_['name'], req('DELETE', '/projects/%s/branches/%s/credentials/%s' % (P, B, c_['token_id'])))
except Exception as e:
    print('clean parse err', e)
if CB:
    req('DELETE', '/projects/%s/branches/%s' % (P, CB))
    print('child branch deleted')
