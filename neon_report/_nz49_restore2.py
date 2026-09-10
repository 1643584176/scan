# -*- coding: utf-8 -*-
"""T4b: 正对照 — T ready 后 restore source=A同项目main(期望成功) + DELETE T 清理 (<=6 req)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
TBID = 'br-withered-cake-w2hwfe53'
MAIN = 'br-wandering-field-w2ob6mpn'
ctx = ssl.create_default_context()

def req(tag, path, body=None, method=None):
    m = method or ('POST' if body is not None else 'GET')
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(m, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            print('== %-30s -> %d  %s' % (tag, r.status, raw[:300].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

# 1) 等 T ready
for i in range(6):
    st, raw = req('T状态', '/projects/%s/branches/%s' % (PA, TBID))
    try:
        state = json.loads(raw).get('branch', {}).get('current_state')
        print('   state =', state)
        if state == 'ready':
            break
    except Exception:
        pass
    time.sleep(5)

# 2) 正对照: restore source=A main
req('restore 同项目main', '/projects/%s/branches/%s/restore' % (PA, TBID),
    {'source_branch_id': MAIN})

# 3) 清理: DELETE T
time.sleep(2)
req('DELETE T', '/projects/%s/branches/%s' % (PA, TBID), method='DELETE')
