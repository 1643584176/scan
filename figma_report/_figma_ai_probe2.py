# -*- coding: utf-8 -*-
"""ActiveAiChatThreadView 完整线程内容读取(B 身份订阅 A 的线程)
id=threadId, ownerId=fileKey(与 FileAiChatThreadsView 同构)
"""
import json, sys, time, websocket
sys.path.insert(0, 'F:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_A, UID_B, FILE_A

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'
THREAD_ID = 'a2f71e01-40c9-4439-9438-e89b23942c21'  # FILE_A 上的 A 线程(XAC-A-file 发现)

client_url = 'https://www.figma.com/file/%s' % FILE_A
url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
       '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
       % (UID_B, client_url))
ws = websocket.create_connection(url, timeout=12, header=['User-Agent: ' + UA, 'Cookie: ' + COOKIE_B])
ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                    'args': {'userId': UID_B, 'anonymousUserId': None},
                    'tags': {'clientType': 'web', 'clientUrl': client_url},
                    'clientRequestedVersion': 2}))
time.sleep(0.5)

for label, args in [
    ('ActiveAiChatThreadView', {'id': THREAD_ID, 'ownerId': FILE_A}),
    ('ActiveAiChatThreadPaginatedView', {'firstPageSize': 20, 'id': THREAD_ID, 'ownerId': FILE_A}),
]:
    ws.send(json.dumps({'messageType': 'subscribe', 'viewName': label,
                        'viewHash': 'abababababababababababababababab',
                        'loadType': 'initial', 'args': args}))
    msgs = []
    ws.settimeout(8)
    try:
        while True:
            msgs.append(ws.recv())
    except Exception:
        pass
    print('### %s %s' % (label, json.dumps(args)[:120]))
    for m in msgs:
        print('   ', m[:600].replace('\n', ' '))
    print()
    time.sleep(1)

ws.close()
