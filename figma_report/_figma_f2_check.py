# -*- coding: utf-8 -*-
"""F2 现状验证:匿名 FileMakeVersionsView 是否已修复 + viewSubscriptionFailed 错误详情"""
import json, time, websocket

FILE_A = 'IHt8kgtR3XmtqU5i8vz7p1'
CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A

def conn(view_name, args, label):
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % CLIENT_URL)
    ws = websocket.create_connection(url, timeout=10, header=['User-Agent: Mozilla/5.0'])
    ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                        'args': {'userId': None, 'anonymousUserId': None},
                        'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
                        'clientRequestedVersion': 2}))
    time.sleep(0.5)
    ws.send(json.dumps({'messageType': 'subscribe', 'viewName': view_name,
                        'viewHash': 'abababababababababababababababab',
                        'loadType': 'initial', 'args': args}))
    msgs = []
    ws.settimeout(6)
    try:
        while True:
            msgs.append(ws.recv())
    except Exception:
        pass
    ws.close()
    print('=== %s ===' % label)
    for m in msgs:
        print('  %s' % m[:600].replace('\n', ' '))
    print()

# 1. F2 的 view(已知存在过)
conn('FileMakeVersionsView', {'fileKey': FILE_A, 'firstPageSize': 10}, 'FileMakeVersionsView(匿名,A文件)')

# 2. 对照:viewSubscriptionFailed 详情(用无效 view 名)
conn('DefinitelyNotARealViewXYZ', {'fileKey': FILE_A}, '无效 view 对照')

# 3. F1 的 view
conn('PlanByFileKey', {'fileKey': FILE_A}, 'PlanByFileKey(匿名,A文件)')
