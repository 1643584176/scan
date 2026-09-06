# -*- coding: utf-8 -*-
"""确认 FILE_A 权限模型 + 解码线程消息内容
1. GET /api/files/{FILE_A}(B cookie) - B 对 A 文件的访问级别
2. 解码已捕获的 contentPb 文本部分
"""
import json, sys, base64, http.client, ssl, gzip, brotli
sys.path.insert(0, 'F:/scan/figma_report')
from _figma_creds import COOKIE_B, FILE_A, FILE_B

HOST = 'www.figma.com'
ORIGIN = 'https://www.figma.com'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'


def req(method, path, cookie=COOKIE_B):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
    hdrs = {'User-Agent': UA, 'Accept-Encoding': 'br, gzip',
            'Origin': ORIGIN, 'Referer': ORIGIN + '/file/%s' % FILE_A}
    if cookie:
        hdrs['Cookie'] = cookie
    conn.request(method, path, headers=hdrs)
    resp = conn.getresponse()
    raw = resp.read()
    enc = resp.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    conn.close()
    return resp.status, raw.decode('utf-8', 'ignore')


for label, fk in [('FILE_A(A)', FILE_A), ('FILE_B(B)', FILE_B)]:
    s, txt = req('GET', '/api/files/%s' % fk)
    print('[%s] %d' % (label, s))
    if s == 200:
        try:
            m = json.loads(txt).get('meta', {})
            print('   key=%s name=%r team_id=%s creator_id=%s' % (
                m.get('key'), (m.get('name') or '')[:60], m.get('team_id'), m.get('creator_id')))
        except Exception as e:
            print('   parse err', e, txt[:150])
    else:
        print('   ', txt[:200].replace('\n', ' '))

print()
print('=== 解码 AI 线程消息 contentPb ===')
# partIndex=0 文本(来自 XAC-A-file 响应)
b64_text = 'CkFDcmVhdGUgdGhlIG5leHQgc2NyZWVuIHRoYXQgZm9sbG93cyB0aGlzIG9uZSBpbiB0aGUgdXNlciBqb3VybmV5Lg=='
raw = base64.b64decode(b64_text)
print('decoded bytes:', raw)
# protobuf 解码尝试:人工剥离长度前缀
print('  str-ish:', repr(raw[2:]) if raw[:1] == b'\n' else repr(raw))
# partIndex=1 是 PNG(data:image/png;base64,...)
b64_part1_head = 'Cv0ICgUxOjgwNhIGU2NyZWVuGgVGUkFNRSEAAAAAAOiSQCkAAAAAAGCIQDLSCGRhdGE6aW1hZ2UvcG5nO2Jhc2U2NCxpVkJPUncwS0dnb0FBQUFOU1VoRVVnQUFBZ0FBQUFGTENBWUFBQUNnRHpUSUFBQUFDWEJJV1hNQUFBc1RBQUFMRXdFQW1wd1lBQUFBQVhOU1IwSUFyczRjNlFBQUFBUm5RVTFCQUFDeGp3djhZUVVBQUFBT2RFVllkRk52Wm5SM1lYSmxBRVpwWjIxaG5yR1dZd0FBQXFoSlJFRlVlQUh0d0FFTkFBQUF3cUQzVDIwT055Z0FBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU'
raw1 = base64.b64decode(b64_part1_head)
print('part1 head bytes:', raw1[:60])
print('  contains data:image/png:', b'data:image/png' in raw1)
