# -*- coding: utf-8 -*-
"""UserLicensesForFile 成员枚举:同一文件(FILE_A)用不同 userId 查,看能否枚举 plan 成员
+ 匿名连接复测(为何失败)
"""
import json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, COOKIE_B

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

# 枚举:同一 fileKey,不同 userId
UID_X1 = '1000000000000000001'  # 随机
UID_X2 = '1666382703778278399'  # A
TESTS = [
    ('UserLicensesForFile', {'fileKey': FILE_A, 'userId': UID_X2}, 'A'),
    ('UserLicensesForFile', {'fileKey': FILE_A, 'userId': UID_B}, 'B'),
    ('UserLicensesForFile', {'fileKey': FILE_A, 'userId': UID_X1}, '随机1'),
    # 用 B 自己的文件对照
    ('UserLicensesForFile', {'fileKey': 'uwNXWhteG3ajjX78QG7a1W', 'userId': UID_A}, 'B文件+A'),
    ('UserLicensesForFile', {'fileKey': 'uwNXWhteG3ajjX78QG7a1W', 'userId': UID_B}, 'B文件+B'),
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
    try:
        j = json.loads(m)
    except Exception:
        print('RAW:', m[:150]); continue
    if j.get('messageType') == 'denormalizedPendingMutations':
        for vk, payload in (j.get('mutations') or {}).items():
            s = json.dumps(payload, ensure_ascii=False)
            if 'currentPlanUser' in s and '"initial":{}' not in s:
                # 提取 currentPlanUser value
                import re as _re
                mm = _re.search(r'"currentPlanUser"[^}]{0,400}', s)
                print(vk[:90])
                print('   ', (mm.group(0)[:380] if mm else s[:380]))
