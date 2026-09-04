# -*- coding: utf-8 -*-
"""匿名 vs B身份:UserLicensesForFile + AiMeterUsageView 对比(FILE_A 公开链接)
验证:这些数据是否只有登录用户能拿(判断泄露边界)
"""
import json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, COOKIE_B

CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A

def run(label, cookie, userId, uid_arg):
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (userId, CLIENT_URL))
    hdrs = ['User-Agent: Mozilla/5.0']
    if cookie:
        hdrs.append('Cookie: ' + cookie)
    ws = websocket.create_connection(url, timeout=10, header=hdrs)
    ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                        'args': {'userId': userId, 'anonymousUserId': None},
                        'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
                        'clientRequestedVersion': 2}))
    time.sleep(0.4)
    for vn, args in [
        ('UserLicensesForFile', {'fileKey': FILE_A, 'userId': uid_arg}),
        ('AiMeterUsageView', {'fileKey': FILE_A}),
        ('PlanByFileKey', {'fileKey': FILE_A}),
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
            print('  RAW:', m[:200]); continue
        mt = j.get('messageType')
        if mt == 'denormalizedPendingMutations':
            for vk, payload in (j.get('mutations') or {}).items():
                vname = json.loads(vk)[0]
                s = json.dumps(payload, ensure_ascii=False)
                # 只显示有实际 value 的
                if 'value":' in s and '"initial":{}' not in s:
                    print('[%s] %s' % (vname, s[:600]))
                else:
                    print('[%s] (空/无值)' % vname)
    print()

# 匿名(无 cookie,uid 参数空)
run('匿名 userId=null', None, '', None)
# B 身份
run('B身份 cookie+uid=B,查询 A 的 license', COOKIE_B, UID_B, UID_A)
# B 身份查询自己
run('B身份 查询自己的 license', COOKIE_B, UID_B, UID_B)
