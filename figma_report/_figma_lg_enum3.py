# -*- coding: utf-8 -*-
"""livegraph 匿名 view 枚举 v3:精确分类 + 完整输出到文件"""
import json, time, websocket, os

FILE_A = 'IHt8kgtR3XmtqU5i8vz7p1'
CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A
OUT = 'D:/scan/figma_report/_lg_enum3.txt'

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
        return '[%s] CONN FAIL %s' % (name, str(e)[:50])
    lines = []
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
        types = set()
        for m in msgs:
            try:
                d = json.loads(m)
                types.add(d.get('messageType', '?'))
                if 'error' in d and d.get('error') is True:
                    types.add('ERROR_TRUE')
            except Exception:
                types.add('RAW')
        has_mut = 'denormalizedPendingMutations' in joined
        has_err = 'ERROR_TRUE' in types or '"messageType":"error"' in joined
        verdict = ''
        if has_mut:
            i = joined.find('denormalizedPendingMutations')
            verdict = '!! MUTATIONS: %s' % joined[i:i+500]
        elif has_err:
            i = joined.find('"messageType":"error"')
            verdict = 'error: %s' % joined[i:i+250]
        else:
            verdict = 'no-data'
        lines.append('[%s] types=%s verdict=%s' % (name, sorted(types), verdict))
        lines.append('  full: %s' % joined[:700].replace('\n', ' '))
    except Exception as e:
        lines.append('[%s] ERR %s' % (name, str(e)[:60]))
    finally:
        try:
            ws.close()
        except Exception:
            pass
    return '\n'.join(lines)

results = []
for name, args in VIEWS:
    results.append(test_view(name, args))
    print(results[-1][:200])
    time.sleep(0.2)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(results))
print('saved ->', OUT)
