# -*- coding: utf-8 -*-
"""H3: restore 并发窗口 — T4 的 restore+DELETE 是否留下幽灵 operation (2 req 只读)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
ctx = ssl.create_default_context()

def req(tag, path):
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request('GET', API_BASE + path, headers=h)
            r = c.getresponse(); raw = r.read(); c.close()
            return r.status, raw
        except Exception as e:
            print('[retry]', tag, e); time.sleep(2)
    return None, None

st, raw = req('最近 operations', '/projects/%s/operations?limit=25' % PA)
if st == 200:
    d = json.loads(raw)
    ops = d.get('operations', [])
    print('operations 总数返回: %d' % len(ops))
    for o in ops:
        print('  id=%s action=%-24s status=%-10s branch=%s endpoint=%s failures=%s created=%s' % (
            o.get('id', '')[:8], o.get('action', ''), o.get('status', ''),
            (o.get('branch_id') or '')[:20], (o.get('endpoint_id') or '')[:20],
            o.get('failures_count'), (o.get('created_at') or '')[:19]))
