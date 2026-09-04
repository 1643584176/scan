# -*- coding: utf-8 -*-
"""B 账号上传测试 + 找 agent-runner 文件列表/会话接口"""
import http.client, ssl, gzip, brotli, json, sys, time, re, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B

ACC_A = '6a979dd2ae93f47d55b62897'
ACC_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_A, method='POST', body=None, headers=None, timeout=20):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if headers: h.update(headers)
    if body is not None and 'Content-Type' not in h:
        h['Content-Type'] = 'application/octet-stream'
    t0 = time.time()
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    b = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:300]
    conn.close()
    return st, dt, b

def show(label, path, ck=COOKIE_A, method='POST', body=None, hdrs=None):
    st, dt, b = req(path, ck, method=method, body=body, headers=hdrs)
    print('%-44s %s %5.1fs | %s' % (label, st, dt, b))

print('== B 账号上传 ==')
show('B+ACC_B upload', '/api/agent-runner-file-upload?accountId=%s&filename=b-probe.txt' % ACC_B,
     COOKIE_B, body=b'hello from B')
show('A+ACC_A upload(对照)', '/api/agent-runner-file-upload?accountId=%s&filename=a-probe.txt' % ACC_A,
     COOKIE_A, body=b'hello from A')

print()
print('== 挖 agent-runner 其他 API 形态 ==')
data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
for key in ['agent-runners', 'agent_runner', 'agentRunner', 'agents/', 'file_key']:
    cnt = 0
    for m in re.finditer(re.escape(key), data):
        s = max(0, m.start() - 350)
        e = min(len(data), m.end() + 350)
        seg = data[s:e].replace('\n', ' ')
        if '/api/' in seg or 'fetch' in seg or 'url' in seg.lower():
            print('--- %s @%d ---' % (key, m.start()))
            print(seg[:650])
            print('-' * 60)
            cnt += 1
            if cnt >= 4:
                break
print('done')
