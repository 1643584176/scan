# -*- coding: utf-8 -*-
"""T4: restore 跨项目 source 验证 — 新建临时分支T, restore source=damp-term(main), 轮询, 清理 (<=8 req)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
PD = 'damp-term-63384673'
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
            print('== %-30s -> %d  %s' % (tag, r.status, raw[:350].decode('utf-8', 'replace')))
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

# 1) damp-term 分支列表 (org key 可读?)
st, raw = req('damp-term branches', '/projects/%s/branches' % PD)
DBID = None
if st == 200:
    try:
        brs = json.loads(raw).get('branches', [])
        for b in brs:
            print('   D分支:', b.get('id'), b.get('name'), b.get('primary'))
        DBID = next((b['id'] for b in brs if b.get('primary')), None)
    except Exception as e:
        print('   parse err', e)

# 2) A 项目建临时分支 T (不带 endpoint, 省资源)
st2, raw2 = req('创建临时分支T', '/projects/%s/branches' % PA, {'branch': {'name': 'sbx-restore-t1'}})
TBID = None
if st2 in (200, 201):
    try:
        TBID = json.loads(raw2).get('branch', {}).get('id')
        print('   TBID =', TBID)
    except Exception:
        pass

# 3) restore: target=T, source=damp-term main (跨项目!)
if TBID and DBID:
    req('restore 跨项目source', '/projects/%s/branches/%s/restore' % (PA, TBID),
        {'source_branch_id': DBID})
