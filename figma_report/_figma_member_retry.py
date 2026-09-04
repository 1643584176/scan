# -*- coding: utf-8 -*-
"""MemberFlyout 系列正确参数重试 + 其他 PlanUser 面"""
import json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, TEAM_A, COOKIE_B

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
    ('MemberFlyoutInfoFromPlanUser', {'planParentId': TEAM_A, 'planParentType': 'Team', 'targetUserId': UID_A}, 'A团队A用户flyout(Team)'),
    ('MemberFlyoutInfoFromPlanUser', {'planParentId': TEAM_A, 'planParentType': 'TEAM', 'targetUserId': UID_A}, 'A团队A用户flyout(TEAM)'),
    ('MemberFlyoutInfoView', {'planId': TEAM_A, 'planType': 'team', 'targetUserId': UID_A}, 'A团队A用户flyoutV2(team)'),
    ('MemberFlyoutInfoView', {'planId': TEAM_A, 'planType': 'Team', 'targetUserId': UID_A}, 'A团队A用户flyoutV2(Team)'),
    ('UserSettingsPlanRow', {'planParentId': TEAM_A, 'planType': 'team'}, 'A团队plan设置行'),
    ('UserSettingsPlanRow', {'planParentId': TEAM_A, 'planType': 'Team'}, 'A团队plan设置行(Team)'),
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
    print(m[:1100].replace('\n', ' '))
    print()
