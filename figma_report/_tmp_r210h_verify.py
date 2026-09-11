# -*- coding: utf-8 -*-
# r210h: 验证——CID 集合 export + WS 对照（RuEdaoh 文件 vs FK2 空）
import sys, io, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3, websocket
urllib3.disable_warnings()

BASE = 'https://www.figma.com'
UID_A = '1666382703778278399'
FKEY_OLD = 'RuEdaohBLXN48WdkzS66BY'   # r194b 建集合的文件
CID = 'd365565a-bc01-4ace-8e85-813572319367'
COOKIE_A = open('_waf_cookies_new.txt', encoding='utf-8').read().strip()
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0')

s = requests.Session()
s.headers.update({'User-Agent': UA, 'X-Figma-User-ID': UID_A, 'Origin': BASE,
                  'Referer': f'{BASE}/', 'Cookie': COOKIE_A, 'Accept': 'application/json'})
try: s.trust_env = False
except Exception: pass

# 1. export（已知集合是否存活）
try:
    r = s.get(f'{BASE}/api/collections/{CID}/export', timeout=40)
    print('[E1_export]', r.status_code, 'len=', len(r.content), flush=True)
    print('   ', r.content[:400].decode('utf-8', 'replace').replace('\n', ' '), flush=True)
except Exception as e:
    print('[E1_export] EXC', repr(e)[:120], flush=True)
time.sleep(1.5)

# 2. WS 对照
HASH = '54ad31928b3e65843187f51739ef6179b7c460af54f9c7766f167b97483472b3'
def ws_check(fk):
    cu = f'https://www.figma.com/file/{fk}'
    url = ('wss://www.figma.com/api/livegraph?pv=1&userId=%s&anonUserId=&clientType=web'
           '&preload=%%7B%%7D&requestedProtocolVersion=2&clientUrl=%s&connectionType=initial&reconnect=0'
           % (UID_A, cu))
    hdr = ['User-Agent: Mozilla/5.0', 'Cookie: ' + COOKIE_A]
    try:
        ws = websocket.create_connection(url, timeout=15, header=hdr)
    except Exception as e:
        print(f'  [{fk}] WS CONNECT ERR {repr(e)[:120]}'); return
    ws.send(json.dumps({'messageType': 'auth', 'clientType': 'web',
                        'args': {'userId': UID_A, 'anonymousUserId': None},
                        'tags': {'clientType': 'web', 'clientUrl': cu}, 'clientRequestedVersion': 2}))
    time.sleep(0.6)
    ws.send(json.dumps({'messageType': 'subscribe', 'viewName': 'ListCollectionsView',
                        'viewHash': HASH, 'loadType': 'initial', 'args': {'fileKey': fk}}))
    ws.settimeout(12)
    t0 = time.time(); got = []
    while time.time() - t0 < 18:
        try:
            m = ws.recv()
        except Exception:
            break
        try:
            j = json.loads(m)
        except Exception:
            continue
        mt = j.get('messageType', '')
        if mt in ('denormalizedPendingMutations', 'mutation'):
            got.append(json.dumps(j, ensure_ascii=False))
        elif mt == 'viewSubscriptionFailed':
            got.append('FAIL ' + str(j)[:200])
    ws.close()
    print(f'  [{fk}] messages={len(got)}')
    for g in got[:3]:
        print('   >', g[:1200])

ws_check(FKEY_OLD)
time.sleep(2)
print('DONE210h')
