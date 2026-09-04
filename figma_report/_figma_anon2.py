# -*- coding: utf-8 -*-
"""匿名连接复测:匿名能否拿 currentPlanUser / AiMeterUsage / 缩略图
三种连接方式对比
"""
import json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, COOKIE_B

CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A

def run(label, cookie, userId):
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (userId, CLIENT_URL))
    hdrs = ['User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0']
    if cookie:
        hdrs.append('Cookie: ' + cookie)
    try:
        ws = websocket.create_connection(url, timeout=8, header=hdrs)
    except Exception as e:
        print('######## %s ########' % label)
        print('  CONN ERR:', e)
        print()
        return
    ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                        'args': {'userId': userId or None, 'anonymousUserId': None},
                        'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
                        'clientRequestedVersion': 2}))
    time.sleep(0.5)
    for vn, args in [
        ('UserLicensesForFile', {'fileKey': FILE_A, 'userId': UID_A}),
        ('AiMeterUsageView', {'fileKey': FILE_A}),
        ('PageThumbnailsByFileKeyView', {'fileKey': FILE_A}),
    ]:
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
    print('######## %s ########' % label)
    for m in msgs:
        try:
            j = json.loads(m)
        except Exception:
            print('  RAW:', m[:150]); continue
        mt = j.get('messageType')
        if mt == 'authSuccess':
            print('  auth: userId=%s anon=%s' % (j.get('userId'), j.get('anonymousUserId')))
        elif mt == 'denormalizedPendingMutations':
            for vk, payload in (j.get('mutations') or {}).items():
                vname = json.loads(vk)[0]
                s = json.dumps(payload, ensure_ascii=False)
                if '"value":' in s and '"initial":{}' not in s:
                    print('  [%s] %s' % (vname, s[:500]))
                else:
                    print('  [%s] 空' % vname)
        elif mt == 'viewSubscriptionFailed':
            print('  FAIL:', j.get('errorCode'))
    print()

run('匿名1(无cookie uid空)', None, '')
run('匿名2(无cookie 声称A)', None, UID_A)
run('B身份(带cookie)', COOKIE_B, UID_B)
