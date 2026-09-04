# -*- coding: utf-8 -*-
"""1. 找 OL 枚举定义(planType 值) 2. UserMonetizationMetadata 完整响应 + MemberFlyout 重试"""
import re, json, time, websocket, sys
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A, TEAM_A, COOKIE_B

d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()
# OL 定义
for m in list(re.finditer(r'(?:let|var|const)\s+OL\s*=\s*\{[^}]{0,300}\}', d))[:3]:
    print('OL def:', m.group(0)[:330])
for m in list(re.finditer(r'OL\s*=\s*\{[^}]{0,300}\}', d))[:3]:
    print('OL def2:', m.group(0)[:330])
# 找 "TEAM" 和 "ORG" 作为枚举值
for m in list(re.finditer(r'[Oo][Rr][Gg]\s*:\s*"[a-zA-Z_]+"\s*,?\s*[Tt][Ee][Aa][Mm]\s*:\s*"[a-zA-Z_]+"', d))[:5]:
    print('enum pair:', m.group(0))
for m in list(re.finditer(r'[Tt][Ee][Aa][Mm]\s*:\s*"[a-zA-Z_]+"\s*,?\s*[Oo][Rr][Gg]\s*:\s*"[a-zA-Z_]+"', d))[:5]:
    print('enum pair2:', m.group(0))

print()
# UserMonetizationMetadata 完整响应
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
# MemberFlyout 重试(planType=TEAM 大写)
for vn, args in [
    ('MemberFlyoutInfoFromPlanUser', {'planParentId': TEAM_A, 'planParentType': 'TEAM', 'targetUserId': UID_A}),
    ('MemberFlyoutInfoView', {'planId': TEAM_A, 'planType': 'TEAM', 'targetUserId': UID_A}),
    ('UserMonetizationMetadata', {'userId': UID_A}),
    ('UserMonetizationMetadata', {'userId': UID_B}),
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
for m in msgs:
    print(m[:900].replace('\n', ' '))
    print()
