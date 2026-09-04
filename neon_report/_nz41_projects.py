# -*- coding: utf-8 -*-
"""org 项目完整清单 + A key 对 damp-term 的访问性 (5 req 只读)"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
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

st, raw = req('org 项目列表', '/projects?org_id=org-flat-dawn-91601224')
if st == 200:
    d = json.loads(raw)
    for p in d.get('projects', []):
        print('ORG 项目: id=%s name=%s created=%s' % (p['id'], p.get('name'), p.get('created_at')))
    ids = [p['id'] for p in d.get('projects', [])]
    print('TOTAL:', len(ids))
else:
    print('列表失败', st, raw[:300])

# A key 访问同 org 历史项目 damp-term-63384673 (若存在)
st2, raw2 = req('damp-term', '/projects/damp-term-63384673')
print('\nA key -> damp-term-63384673 : %d %s' % (st2, raw2[:200].decode('utf-8', 'replace') if raw2 else ''))
