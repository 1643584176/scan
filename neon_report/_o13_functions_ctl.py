# -*- coding: utf-8 -*-
"""Neon Functions 控制面端点实测(Beta 面):
1. list/get 基线 + 不存在 slug 错误形态
2. 无权限用户对照(鉴权模型)
3. deployments 错误形态(multipart 要求)
4. custom-domains list + 注册校验(域名规则/所有权验证)"""
import http.client, ssl, json, random, string

ctx = ssl.create_default_context()
HOST = 'console-stage.neon.build'
PID = 'orange-sun-90493739'
BID = 'br-wandering-field-w2ob6mpn'
COOKIE_RAW = None

# 从 _neon_creds_stage.py 导入 cookie
import importlib.util
spec = importlib.util.spec_from_file_location('ncs', 'D:/scan/neon_report/_neon_creds_stage.py')
ncs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ncs)
COOKIE_RAW = ncs.cookie_str()
HDR_TEST = ncs.HEADERS_TEST

def req(cookie, method, path, body=None, ctype='application/json', extra=None):
    try:
        conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Cookie': cookie, 'X-Bug-Bounty': 'xxbo'}
        if ctype:
            h['Content-Type'] = ctype
        if extra:
            h.update(extra)
        data = body.encode() if isinstance(body, str) else (json.dumps(body).encode() if body is not None else None)
        conn.request(method, '/api/v2' + path, body=data, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        out = raw.decode('utf-8', 'replace')
        conn.close()
        return st, out
    except Exception as e:
        return -1, 'EXC %s' % e

print('=== [1] functions list/get 基线 ===', flush=True)
st, raw = req(COOKIE_RAW, 'GET', '/projects/%s/branches/%s/functions' % (PID, BID))
print('list functions -> %d %s' % (st, raw[:400].replace('\n', ' ')), flush=True)

slug = 'zz' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
st, raw = req(COOKIE_RAW, 'GET', '/projects/%s/branches/%s/functions/%s' % (PID, BID, slug))
print('get bogus slug -> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)

st, raw = req(COOKIE_RAW, 'PATCH', '/projects/%s/branches/%s/functions/%s' % (PID, BID, slug),
              {'name': 'x'})
print('patch bogus slug -> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)

st, raw = req(COOKIE_RAW, 'DELETE', '/projects/%s/branches/%s/functions/%s' % (PID, BID, slug))
print('delete bogus slug -> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)

print('\n=== [2] deployments 错误形态 ===', flush=True)
# 无 body / 空 json / multipart 空
st, raw = req(COOKIE_RAW, 'POST', '/projects/%s/branches/%s/functions/%s/deployments' % (PID, BID, slug))
print('deploy no body -> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)
st, raw = req(COOKIE_RAW, 'POST', '/projects/%s/branches/%s/functions/%s/deployments' % (PID, BID, slug), {})
print('deploy empty json -> %d %s' % (st, raw[:300].replace('\n', ' ')), flush=True)

print('\n=== [3] custom-domains ===', flush=True)
st, raw = req(COOKIE_RAW, 'GET', '/projects/%s/branches/%s/custom-domains' % (PID, BID))
print('list custom-domains -> %d %s' % (st, raw[:400].replace('\n', ' ')), flush=True)

# 域名注册校验矩阵
for dom in ['example.com', 'evil-' + ''.join(random.choices(string.ascii_lowercase, k=6)) + '.com',
            'sub.example.org', 'foo.neon.build']:
    st, raw = req(COOKIE_RAW, 'POST', '/projects/%s/branches/%s/custom-domains' % (PID, BID),
                  {'domain': dom, 'entity_type': 'function', 'entity_id': 'fn-not-exist'})
    print('register %s -> %d %s' % (dom, st, raw[:300].replace('\n', ' ')), flush=True)

print('\n=== [4] 授权对照:无 project 权限用户(na2 有自己 project?) ===', flush=True)
# na2 cookie:登录 nauth 拿不到 console;用 na2 的 keycloak token 试?简化:直接看错误是否区分 403
# 用错误 project id
st, raw = req(COOKIE_RAW, 'GET', '/projects/does-not-exist-0000/branches/%s/functions' % BID)
print('wrong pid -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)
st, raw = req(COOKIE_RAW, 'GET', '/projects/%s/branches/br-does-not-exist-0000/functions' % PID)
print('wrong bid -> %d %s' % (st, raw[:200].replace('\n', ' ')), flush=True)
