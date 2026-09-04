# -*- coding: utf-8 -*-
"""multiplayer WS:保存原始帧,分析 fig-wire 协议结构"""
import json, time, sys, http.client, ssl, gzip, brotli, websocket
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_B, FILE_A, COOKIE_B

# 1. realtime_token(匿名)
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('www.figma.com', context=ctx, timeout=20)
conn.request('GET', '/api/file_metadata/%s' % FILE_A,
             headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip'})
resp = conn.getresponse()
body = resp.read()
enc = resp.getheader('Content-Encoding')
if enc == 'br':
    body = brotli.decompress(body)
meta = json.loads(body.decode('utf-8', 'ignore'))
rt = meta.get('meta', {}).get('realtime_token', '')

# 2. 连接
url = ('wss://www.figma.com/api/multiplayer/%s?role=viewer&tracking_session_id=test456&version=221'
       '&recentReload=0&file-load-streaming-compression&user-id=&client_release=24850ed350d86c5466f8b775996885ec28db9f19'
       '&realtime_token=%s' % (FILE_A, rt))
ws = websocket.create_connection(url, timeout=8, header=['User-Agent: Mozilla/5.0'])
msgs = []
ws.settimeout(5)
try:
    while True:
        msgs.append(ws.recv())
except Exception:
    pass
ws.close()
print('frames:', len(msgs))

out = open(r'D:\scan\figma_report\_js\mp_frames.bin', 'wb')
out2 = open(r'D:\scan\figma_report\_js\mp_frames.txt', 'w', encoding='utf-8')
for i, m in enumerate(msgs):
    if isinstance(m, str):
        b = m.encode('utf-8')
    else:
        b = m
    out.write(len(b).to_bytes(4, 'big'))
    out.write(b)
    hx = b[:64].hex()
    out2.write('--- frame %d len=%d ---\n' % (i, len(b)))
    out2.write(hx + '\n')
    # 尝试 ASCII 显示
    asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in b[:128])
    out2.write(asc + '\n\n')
out.close()
out2.close()
print('saved')

# 3. 帧结构分析
print()
print('=== 帧结构 ===')
for i, m in enumerate(msgs):
    if isinstance(m, str):
        b = m.encode('utf-8')
    else:
        b = m
    print('frame %d: len=%d head=%s' % (i, len(b), b[:16].hex()))
    asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in b[:48])
    print('   asc:', asc)
