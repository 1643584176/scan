# -*- coding: utf-8 -*-
"""影响面测试:
1. 公开文件(ucha7bf05fJ81CJZVoruo0 Flowbite)FileAiChatThreadsView - B 身份
2. 匿名订阅 FILE_A / 公开文件 - 是否无需登录
3. 扫描 chunk 找 privacyMode 枚举与 AI 线程可见性 UI 文案
"""
import json, sys, time, websocket, os, re
sys.path.insert(0, 'F:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_B

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'
PUBLIC_FILE = 'ucha7bf05fJ81CJZVoruo0'   # Flowbite(公开,PlanByFileKey 验证过)
FILE_A = 'IHt8kgtR3XmtqU5i8vz7p1'        # A 的私有共享文件


def lg_test(uid, file_key, cookie, label, views):
    client_url = 'https://www.figma.com/file/%s' % file_key
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (uid, client_url))
    try:
        hdr = ['User-Agent: ' + UA]
        if cookie:
            hdr.append('Cookie: ' + cookie)
        ws = websocket.create_connection(url, timeout=10, header=hdr)
    except Exception as e:
        print('### %s connect FAIL %s' % (label, e))
        return
    ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                        'args': {'userId': uid, 'anonymousUserId': None},
                        'tags': {'clientType': 'web', 'clientUrl': client_url},
                        'clientRequestedVersion': 2}))
    time.sleep(0.4)
    for vn, args in views:
        ws.send(json.dumps({'messageType': 'subscribe', 'viewName': vn,
                            'viewHash': 'abababababababababababababababab',
                            'loadType': 'initial', 'args': args}))
        msgs = []
        ws.settimeout(5)
        try:
            while True:
                msgs.append(ws.recv())
        except Exception:
            pass
        print('### %s | %s %s' % (label, vn, json.dumps(args)[:100]))
        for m in msgs:
            # 摘要:统计线程/消息数量而不是全量打印
            if 'AiChatThread' in m:
                n_thread = m.count('"userId"')
                has_msg = '"AiChatMessage"' in m
                has_part = '"AiMessagePart"' in m
                snippet = m[:400].replace('\n', ' ')
                print(f'   [threads~{n_thread} msgs={has_msg} parts={has_part}] {snippet}...')
            elif 'viewSubscriptionFailed' in m or 'error' in m.lower():
                print('   ERR:', m[:300])
            else:
                print('   ', m[:300].replace('\n', ' '))
        print()
    ws.close()


print('========== 1. B 身份订阅公开文件(Flowbite) ==========')
lg_test(UID_B, PUBLIC_FILE, COOKIE_B, 'PUB-Flowbite',
        [('FileAiChatThreadsView', {'ownerId': PUBLIC_FILE})])
time.sleep(2)

print('========== 2. 匿名订阅 FILE_A(私有) ==========')
lg_test('', FILE_A, None, 'ANON-FILE_A',
        [('FileAiChatThreadsView', {'ownerId': FILE_A})])
time.sleep(2)

print('========== 3. 匿名订阅公开文件(Flowbite) ==========')
lg_test('', PUBLIC_FILE, None, 'ANON-Flowbite',
        [('FileAiChatThreadsView', {'ownerId': PUBLIC_FILE})])
time.sleep(2)

print('========== 4. chunks 中 privacyMode/AI 可见性 ==========')
JS = r'F:/scan/figma_report/_js'
for fn in sorted(os.listdir(JS)):
    if not fn.endswith('.js') or fn.startswith('figma_app'):
        continue
    try:
        c = open(os.path.join(JS, fn), encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    if 'privacyMode' in c or 'fileAiChatThreads' in c or 'Your threads' in c:
        print('--', fn)
        for m in list(re.finditer(r'[^,;{}]{0,120}privacyMode[^,;{}]{0,120}', c))[:5]:
            print('   privacyMode:', m.group(0)[:240].replace('\n', ' '))
        for m in list(re.finditer(r'["\'](?:Your threads|your threads|Threads|Private|Only visible)[^"\']{0,40}["\']', c))[:5]:
            print('   UI:', m.group(0)[:120])
