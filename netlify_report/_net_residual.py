# -*- coding: utf-8 -*-
"""真实资源 body 盲扫(安全端点) + audit 参数 + traffic_splits/snippets/metadata 形态"""
import http.client, ssl, gzip, brotli, json, sys, random, string, re
import yaml
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, TOKEN_B

ctx = ssl.create_default_context()
SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ACC_A = '6a979dd2ae93f47d55b62897'

def req(method, path, body=None, token=TOKEN_A, timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if body is not None:
        h['Content-Type'] = 'application/json'
    if token: h['Authorization'] = 'Bearer ' + token
    b = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    txt = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, txt

def probe(tag, m, p, body=None, tok=TOKEN_A):
    st, b = req(m, p, body, tok)
    print('%-58s %s | %s' % (tag, st, b[:250].replace('\n', ' ')))
    return st, b

rnd = ''.join(random.choices(string.ascii_lowercase, k=6))
print('== 1. metadata PUT 形态 ==')
probe('PUT metadata {}', 'PUT', '/api/v1/sites/%s/metadata' % SITE_A, {'zz': 'v'})
st, b = probe('GET metadata 确认', 'GET', '/api/v1/sites/%s/metadata' % SITE_A)
# 清回空
probe('PUT metadata 清空', 'PUT', '/api/v1/sites/%s/metadata' % SITE_A, {})
print()
print('== 2. snippets PUT 形态 ==')
for body in [
    {'id': 'head', 'title': 'zz', 'content': '<script>zz</script>'},
    {'title': 'zz-%s' % rnd, 'content': '<b>zz</b>'},
]:
    st, b = probe('PUT snippets %s' % list(body.keys()), 'PUT',
                  '/api/v1/sites/%s/snippets' % SITE_A, body)
    if st in (200, 201):
        st2, b2 = req('GET', '/api/v1/sites/%s/snippets' % SITE_A)
        print('   GET snippets now:', b2[:200])
        # 清理
        st3, b3 = req('PUT', '/api/v1/sites/%s/snippets' % SITE_A, [])
        print('   cleanup:', st3, b3[:100])
        break
print()
print('== 3. audit 参数 ==')
for q in ['', '?limit=5', '?type=site', '?until=2027-01-01', '?max_entries=5']:
    st, b = probe('GET audit%s' % q, 'GET', '/api/v1/accounts/%s/audit%s' % (ACC_A, q))
print()
print('== 4. traffic_splits 形态 ==')
for body in [
    {},
    {'split_test': {'active': True}},
    {'active': True, 'percentage': 50},
]:
    st, b = probe('POST traffic_splits %s' % list(body.keys()), 'POST',
                  '/api/v1/sites/%s/traffic_splits' % SITE_A, body)
    if st in (200, 201):
        print('   !! created, body:', b[:300])
        break
st, b = probe('GET traffic_splits', 'GET', '/api/v1/sites/%s/traffic_splits' % SITE_A)
print()
print('== 5. deploys 相关残余: lock/restore 用真实 deploy ==')
DID = '6a97c9e3083c963fd210b895'
probe('POST lock', 'POST', '/api/v1/deploys/%s/lock' % DID, {})
probe('POST unlock(恢复)', 'POST', '/api/v1/deploys/%s/unlock' % DID, {})
print('done')
