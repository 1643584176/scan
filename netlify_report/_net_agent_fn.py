# -*- coding: utf-8 -*-
"""filename 消毒测试(B 账号有 credits):穿越/嵌套/特殊字符在 file_key 的反映"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_B

ACC_B = '6a97b6454fef0db964f75db6'
ctx = ssl.create_default_context()

def req(path, cookie=COOKIE_B, method='POST', body=None, timeout=25):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json'}
    if cookie: h['Cookie'] = cookie
    if body is not None:
        h['Content-Type'] = 'text/plain'
    t0 = time.time()
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    st = r.status
    b = raw.decode('utf-8', 'ignore').replace('\n', ' ')[:250]
    conn.close()
    return st, dt, b

def up(fn, body=b'z'):
    p = '/api/agent-runner-file-upload?accountId=%s&filename=%s' % (ACC_B, urllib.parse.quote(fn, safe=''))
    st, dt, b = req(p, body=body)
    print('%-30r -> %s %5.1fs | %s' % (fn, st, dt, b))
    return b

print('== filename 消毒 ==')
up('plain.txt')
up('../escape.txt')
up('a/../b.txt')
up('../../up2.txt')
up('dir/sub/file.txt')
up('....//mixed.txt')
up('a%2Fb.txt')          # quote 后再编码 -> %252F
up('..\\win.txt')
up('x' * 300 + '.txt')   # 超长
up('.hidden')
up('..')
up('...')
up('user-uploaded-content/6a97b6454fef0db964f75db6')  # 尝试直接指定前缀?
print('done')
