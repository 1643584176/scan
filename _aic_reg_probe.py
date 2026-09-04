# -*- coding: utf-8 -*-
"""AIC Registration 树:完整 callbacks 结构 + 尝试注册第二账号"""
import requests, urllib3, json
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
URL = BASE + '/am/json/realms/alpha/authenticate?authIndexType=service&authIndexValue=Registration'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
H = {'User-Agent': 'research-1643',
     'Accept-API-Version': 'resource=1.0, protocol=1.0',
     'Content-Type': 'application/json'}

r = S.post(URL, json={}, timeout=15, verify=False, headers=H)
d = r.json()
authId = d.get('authId')
print('init:', r.status_code)
for cb in d.get('callbacks', []):
    print('\n### %s _id=%s' % (cb['type'], cb.get('_id')))
    for o in cb.get('output', []):
        v = o.get('value')
        vs = json.dumps(v) if not isinstance(v, str) else v
        print('  OUT %-20s = %s' % (o.get('name'), vs[:300]))
    for i in cb.get('input', []):
        print('  IN  %-20s = %s' % (i.get('name'), str(i.get('value'))[:100]))
