# -*- coding: utf-8 -*-
"""T5b: restore snapshot -> target_branch_id 跨项目(D临时分支) 校验测试 + 清理 (<=7 req)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
PD = 'damp-term-63384673'
SID = 'snap-wild-meadow-w2smd0lu'
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
            print('== %-30s -> %d  %s' % (tag, r.status, raw[:400].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

# 1) D 项目建临时分支 DT
st, raw = req('创建DT分支', '/projects/%s/branches' % PD, {'branch': {'name': 'sbx-snap-dt1'}})
DTID = None
if st in (200, 201):
    try:
        DTID = json.loads(raw).get('branch', {}).get('id')
        print('   DTID =', DTID)
    except Exception:
        pass

# 2) restore A快照 -> target=DT (跨项目)
if DTID:
    req('snapshot restore 跨项目target', '/projects/%s/snapshots/%s/restore' % (PA, SID),
        {'target_branch_id': DTID, 'name': 'sbx-restore-from-snap'})

    # 3) 等 8s 看 DT 状态 (是否被 restore 动作影响)
    time.sleep(8)
    req('DT状态', '/projects/%s/branches/%s' % (PD, DTID))

# 4) 清理: DELETE DT + DELETE snapshot
time.sleep(2)
req('DELETE DT', '/projects/%s/branches/%s' % (PD, DTID), method='DELETE')
req('DELETE snapshot', '/projects/%s/snapshots/%s' % (PA, SID), method='DELETE')
