# -*- coding: utf-8 -*-
"""multiplayer WS 测试:匿名 + realtime_token 连接 A 文件
URL 构造来自 early.js: /api/multiplayer/{fileKey}?role=&tracking_session_id=&version=221&user-id=&client_release=
"""
import json, time, sys, http.client, ssl, gzip, brotli, websocket
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, COOKIE_B

# 1. 获取 realtime_token(匿名)
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('www.figma.com', context=ctx, timeout=20)
conn.request('GET', '/api/file_metadata/%s' % FILE_A,
             headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip'})
resp = conn.getresponse()
body = resp.read()
enc = resp.getheader('Content-Encoding')
if enc == 'br':
    body = brotli.decompress(body)
elif enc == 'gzip':
    body = gzip.decompress(body)
meta = json.loads(body.decode('utf-8', 'ignore'))
print('meta status:', resp.status)
print('realtime_token:', meta.get('meta', {}).get('realtime_token', '')[:80])
print('pass_state:', meta.get('meta', {}).get('pass_state', '')[:120])
rt = meta.get('meta', {}).get('realtime_token', '')

# 2. 尝试各种连接参数
def try_mp(label, url, headers):
    try:
        ws = websocket.create_connection(url, timeout=8, header=headers)
    except Exception as e:
        print('[%s] CONN ERR: %s' % (label, str(e)[:120]))
        return
    msgs = []
    ws.settimeout(5)
    try:
        while True:
            msgs.append(ws.recv())
    except Exception:
        pass
    ws.close()
    print('[%s] msgs: %d' % (label, len(msgs)))
    for m in msgs[:3]:
        print('   ', m[:300])
    print()

# a. 匿名 viewer,带 realtime_token 参数
url_a = ('wss://www.figma.com/api/multiplayer/%s?role=viewer&tracking_session_id=test123&version=221'
         '&recentReload=0&file-load-streaming-compression&user-id=%s&client_release=24850ed350d86c5466f8b775996885ec28db9f19'
         '&realtime_token=%s' % (FILE_A, '', rt))
try_mp('匿名viewer+token', url_a, ['User-Agent: Mozilla/5.0'])

# b. 带 cookie(B 身份)viewer
url_b = ('wss://www.figma.com/api/multiplayer/%s?role=viewer&tracking_session_id=test123&version=221'
         '&recentReload=0&file-load-streaming-compression&user-id=%s&client_release=24850ed350d86c5466f8b775996885ec28db9f19'
         % (FILE_A, UID_B))
try_mp('B身份viewer', url_b, ['User-Agent: Mozilla/5.0', 'Cookie: ' + COOKIE_B])

# c. B 身份 editor 角色(尝试)
url_c = ('wss://www.figma.com/api/multiplayer/%s?role=editor&tracking_session_id=test123&version=221'
         '&recentReload=0&file-load-streaming-compression&user-id=%s&client_release=24850ed350d86c5466f8b775996885ec28db9f19'
         % (FILE_A, UID_B))
try_mp('B身份editor', url_c, ['User-Agent: Mozilla/5.0', 'Cookie: ' + COOKIE_B])
