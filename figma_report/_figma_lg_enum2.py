# -*- coding: utf-8 -*-
"""livegraph 匿名 view 枚举 v2:等待数据流,按 denormalizedPendingMutations 分类
只测核心候选(文件内容/评论/AI/团队/分享)
"""
import json, time, websocket

FILE_A = 'IHt8kgtR3XmtqU5i8vz7p1'
CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A

VIEWS = [
    ('FileView', {'fileKey': FILE_A}),
    ('FileMetaView', {'fileKey': FILE_A}),
    ('FileVersionsView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('VersionView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('CommentsView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('CommentView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('FileCommentsView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('AiThreadView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('AiChatView', {'fileKey': FILE_A, 'firstPageSize': 10}),
    ('TeamView', {'teamId': '1666382706663462213'}),
    ('TeamUsersView', {'teamId': '1666382706663462213'}),
    ('UserView', {'userId': '1666382703778278399'}),
    ('SharedUsersView', {'fileKey': FILE_A}),
    ('FolderView', {'folderId': '634606970'}),
    ('FileShareView', {'fileKey': FILE_A}),
    ('MakeVersionsView', {'fileKey': FILE_A}),
    ('PlanView', {'fileKey': FILE_A}),
    ('LibraryView', {'fileKey': FILE_A}),
]

def test_view(name, args):
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % CLIENT_URL)
    try:
        ws = websocket.create_connection(url, timeout=10, header=['User-Agent: Mozilla/5.0'])
    except Exception as e:
        print('[%s] CONN FAIL %s' % (name, str(e)[:50]))
        return
    try:
        ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                            'args': {'userId': None, 'anonymousUserId': None},
                            'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
                            'clientRequestedVersion': 2}))
        time.sleep(0.5)
        ws.send(json.dumps({'messageType': 'subscribe', 'viewName': name,
                            'viewHash': 'abababababababababababababababab',
                            'loadType': 'initial', 'args': args}))
        msgs = []
        ws.settimeout(5)
        try:
            while True:
                msgs.append(ws.recv())
        except Exception:
            pass
        joined = '\n'.join(msgs)
        if 'denormalizedPendingMutations' in joined:
            # 提取 mutations 部分
            i = joined.find('denormalizedPendingMutations')
            print('[%s] !! MUTATIONS: %s' % (name, joined[i:i+400]))
        elif 'error' in joined.lower():
            print('[%s] error: %s' % (name, joined[:200]))
        else:
            print('[%s] empty (%d msgs)' % (name, len(msgs)))
    except Exception as e:
        print('[%s] ERR %s' % (name, str(e)[:50]))
    finally:
        try:
            ws.close()
        except Exception:
            pass

for name, args in VIEWS:
    test_view(name, args)
    time.sleep(0.2)
