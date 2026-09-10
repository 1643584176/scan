# -*- coding: utf-8 -*-
"""H3b: 确认 br-lively-salad-w28l 是否残留 + 全分支列表 (1 req 只读)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
PA = 'orange-sun-90493739'
ctx = ssl.create_default_context()

for attempt in range(3):
    try:
        c = http.client.HTTPSConnection(API_HOST, timeout=20, context=ctx)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
             'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
        h.update(HEADERS_TEST)
        c.request('GET', API_BASE + '/projects/%s/branches' % PA, headers=h)
        r = c.getresponse(); raw = r.read(); c.close()
        print('status:', r.status)
        d = json.loads(raw)
        for b in d.get('branches', []):
            print('  id=%-28s name=%-20s state=%-10s parent=%s created=%s' % (
                b['id'], b.get('name'), b.get('current_state'),
                (b.get('parent_id') or '')[:20], b.get('created_at', '')[:19]))
        print('TOTAL:', len(d.get('branches', [])))
        break
    except Exception as e:
        print('[retry]', e); time.sleep(2)
