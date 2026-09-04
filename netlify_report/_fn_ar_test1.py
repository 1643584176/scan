# -*- coding: utf-8 -*-
"""Netlify:agent-runner 文件上传/删除 基线测试(账号 A 自产自销)"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, TOKEN_A
ctx = ssl.create_default_context()

ACC_UUID = '6a979dd2ae93f47d55b62897'   # A team uuid
ACC_SLUG = '1643584176'                  # A team slug

def req(host, path, method='POST', body=None, headers=None, raw=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept': 'application/json', 'Cookie': COOKIE_A}
    if headers:
        h.update(headers)
    conn.request(method, path, body=raw if raw is not None else body, headers=h)
    r = conn.getresponse(); raw2 = r.read()
    st = r.status; conn.close()
    return st, raw2[:400].decode('utf-8', 'replace')

fname = 'ar-test-%d.txt' % int(time.time())
content = b'netlify ar test file\n'

for acc, tag in [(ACC_UUID, 'uuid'), (ACC_SLUG, 'slug')]:
    print('=== upload accountId=%s (%s) ===' % (acc, tag))
    p = '/api/agent-runner-file-upload?accountId=%s&filename=%s' % (acc, fname)
    s, b = req('api.netlify.com', p, raw=content,
               headers={'Content-Type': 'text/plain'})
    print('status:', s, '|', b[:200])
    fk = None
    try:
        fk = json.loads(b).get('file_key')
    except Exception:
        pass
    print('file_key:', fk)
    if fk:
        # 删除同账号文件
        p2 = '/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (acc, fk)
        s2, b2 = req('app.netlify.com', p2)
        print('delete ->', s2, '|', b2[:200])
