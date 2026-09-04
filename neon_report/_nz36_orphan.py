# -*- coding: utf-8 -*-
"""查 br-proud-river-w2ff1c5d 来源(creation_source/状态) 后删除"""
import http.client, ssl, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
B = 'br-proud-river-w2ff1c5d'

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
            print('== %s -> %d | %s' % (tag, r.status, raw[:900].decode('utf-8', errors='replace')))
            return r.status, raw
        except Exception as e:
            print('[retry %s]' % tag, e); time.sleep(2)
    return None, None

req('detail', '/projects/%s/branches/%s' % (P, B), method='GET')
req('anon-status', '/projects/%s/branches/%s/anonymized_status' % (P, B), method='GET')
req('del', '/projects/%s/branches/%s' % (P, B), method='DELETE')
time.sleep(2)
req('branches-final', '/projects/%s/branches' % P, method='GET')
