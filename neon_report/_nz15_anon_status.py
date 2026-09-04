# -*- coding: utf-8 -*-
"""查脱敏分支状态/规则 + 启动 anonymize"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
BR1 = 'br-late-lab-w2z537vl'      # 空 body 分支
BR2 = 'br-proud-haze-w2hel016'    # 带 email masking rule 分支

def req(tag, path, body=None, method=None):
    m = method or ('POST' if body is not None else 'GET')
    for attempt in range(3):
        try:
            c = http.client.HTTPSConnection(API_HOST, timeout=25, context=ctx)
            h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
            h.update(HEADERS_TEST)
            c.request(m, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
            r = c.getresponse(); raw = r.read()
            c.close()
            print('\n== %s -> %d' % (tag, r.status))
            print(raw[:1000].decode('utf-8', errors='replace'))
            return r.status, raw
        except Exception as e:
            print('[retry %s]' % tag, e); time.sleep(2)
    return None, None

for b, tag in ((BR1, 'br1'), (BR2, 'br2')):
    req('%s_status' % tag, '/projects/%s/branches/%s/anonymized_status' % (P, b))
    time.sleep(1)
    req('%s_rules' % tag, '/projects/%s/branches/%s/masking_rules' % (P, b))
    time.sleep(1)
