# -*- coding: utf-8 -*-
import http.client, ssl, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ctx = ssl.create_default_context()
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or list(keyj.values())[0]
ctxb = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx_b.json')))
PID2, BID2 = ctxb['pid2'], ctxb['bid2']
conn = http.client.HTTPSConnection('console-stage.neon.build', context=ctx, timeout=30)
conn.request('GET', '/api/v2/projects/%s/connection_uri?branch_id=%s&database_name=neondb&role_name=neondb_owner' % (PID2, BID2),
             headers={'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo', 'User-Agent': 'Mozilla/5.0'})
r = conn.getresponse()
raw = r.read().decode('utf-8', 'replace')
print(r.status)
print(raw[:800])
