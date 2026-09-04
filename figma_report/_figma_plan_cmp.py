# -*- coding: utf-8 -*-
"""对照测试:TeamByIdForPlanView 对 任意/随机 teamId 是否返回 planPublicInfo
+ A 的第二个文件测试(如果知道 key)
"""
import json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, TEAM_A, TEAM_B, COOKIE_B

CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A
url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
       '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
       % (UID_B, CLIENT_URL))
ws = websocket.create_connection(url, timeout=10, header=['User-Agent: Mozilla/5.0', 'Cookie: ' + COOKIE_B])
ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                    'args': {'userId': UID_B, 'anonymousUserId': None},
                    'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
                    'clientRequestedVersion': 2}))
time.sleep(0.4)

TESTS = [
    ('TeamByIdForPlanView', {'teamId': TEAM_A}, 'A团队plan(已知泄露)'),
    ('TeamByIdForPlanView', {'teamId': TEAM_B}, 'B自己团队plan(对照)'),
    ('TeamByIdForPlanView', {'teamId': '1234567890123456789'}, '随机teamId(不存在)'),
    ('TeamByIdForPlanUserView', {'teamId': TEAM_A}, 'A团队planUser(对照)'),
    ('TeamByIdForPlanUserView', {'teamId': TEAM_B}, 'B团队planUser(对照)'),
]
for vn, args, label in TESTS:
    ws.send(json.dumps({'messageType': 'subscribe', 'viewName': vn,
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
for m in msgs:
    print(m[:800].replace('\n', ' '))
    print()
