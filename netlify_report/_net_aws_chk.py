# -*- coding: utf-8 -*-
"""Netlify:验证函数运行时注入的 AWS 临时凭证权限范围
步骤:1) 调用 probe1 获取 AWS_* env;2) 用 boto3 调 sts GetCallerIdentity;3) 枚举只读 API 判断权限边界
凭证掩码输出,完整值仅写本地文件 _aws_creds.json
"""
import http.client, ssl, gzip, brotli, json, sys, os

ctx = ssl.create_default_context()
HOST = 'sec-test-rcf6lz.netlify.app'
CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_aws_creds.json')

def mask(v):
    if not v:
        return ''
    return v[:4] + '...' + v[-4:] if len(v) > 10 else '***'


def get(host, path):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=60)
    conn.request('GET', path, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip'})
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

# 1. 调用函数,取 AWS_* env
st, raw = get(HOST, '/.netlify/functions/probe1')
print('probe1 status:', st)
d = json.loads(raw) if st == 200 else {}
env = d.get('env', {})
print('env keys matched:', list(env.keys()))
aws = {k: v for k, v in env.items() if k.startswith('AWS') or 'AWS' in k.upper()}
if not aws:
    print('!! no AWS_* vars in filtered env, envCount=', d.get('envCount'))
    sys.exit(1)

for k, v in aws.items():
    print(' ', k, '=', mask(str(v)))

creds = {}
for k in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'AWS_REGION', 'AWS_DEFAULT_REGION', 'AWS_LAMBDA_FUNCTION_NAME']:
    if k in env:
        creds[k] = env[k]
with open(CREDS_FILE, 'w', encoding='utf-8') as f:
    json.dump(creds, f, indent=1)
print('saved ->', CREDS_FILE)

# 2. 用 boto3 验证身份
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
try:
    import boto3
except Exception as e:
    print('boto3 missing:', e)
    sys.exit(2)

region = creds.get('AWS_REGION') or creds.get('AWS_DEFAULT_REGION') or 'us-east-1'
sess = boto3.Session(
    aws_access_key_id=creds.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=creds.get('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=creds.get('AWS_SESSION_TOKEN'),
    region_name=region,
)
try:
    sts = sess.client('sts')
    ident = sts.get_caller_identity()
    print('== GetCallerIdentity ==')
    for k, v in ident.items():
        if k in ('ResponseMetadata',):
            continue
        print(' ', k, '=', v)
except Exception as e:
    print('sts err:', str(e)[:500])
    sys.exit(3)
