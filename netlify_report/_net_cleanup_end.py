# -*- coding: utf-8 -*-
"""Netlify 收尾清理:agent-runner 残留文件 + 失败 deploy 壳"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B, TOKEN_B
ctx = ssl.create_default_context()

# 1. 删除 agent-runner 测试残留文件(test3 上传未删的)
ACC_B_UUID = '6a97b6454fef0db964f75db6'
LEFTOVER = 'user-uploaded-content/%s/6e022426-2e9a-4484-9e85-5639de84f40c/ar-x-1788419836.txt' % ACC_B_UUID

def app_req(path, method='POST'):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Cookie': COOKIE_B,
         'Origin': 'https://app.netlify.com'}
    conn.request(method, path, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw[:200].decode('utf-8', 'replace')

s, b = app_req('/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (ACC_B_UUID, LEFTOVER))
print('cleanup agent-runner file:', s, b)

# 2. cancel 失败的 deploy 壳(B site)
def api(path, method='GET', body=None):
    import gzip
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_B, 'Content-Type': 'application/json'}
    conn.request(method, path, body=json.dumps(body).encode() if body else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    if r.getheader('Content-Encoding') == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status; conn.close()
    return st, raw

SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'
# 列出最近 deploys 找 fn-p4 壳
s, raw = api('/api/v1/sites/%s/deploys?per_page=20' % SITE_B)
if s == 200:
    try:
        deploys = json.loads(raw)
        for d in deploys:
            title = (d.get('title') or '')
            if 'fn-p4' in title or 'fn-p4b' in title or 'fn-p4c' in title or 'fn-p4d' in title:
                did = d.get('id')
                st2, b2 = api('/api/v1/deploys/%s/cancel' % did, method='POST', body={})
                print('cancel %s (%s): %d %s' % (did[:12], title, st2, b2[:100]))
    except Exception as e:
        print('parse deploys ERR', str(e)[:120])
else:
    print('list deploys:', s, raw[:100])
