# -*- coding: utf-8 -*-
"""S3 端点 SigV4 签名请求判别(WAF 层 vs 应用层 403)
1. issue storage:read 凭据 -> s3_secret
2. boto3 SigV4 ListObjects/ListBuckets/GetObject(不存在 key -> 看错误码)
3. 无签名对照"""
import http.client, ssl, json, time, os, sys

ctx = ssl.create_default_context()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import API_HOST, API_BASE
keyj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_apikey.json')))
KEY = keyj.get('key') or keyj.get('api_key') or keyj.get('token') or list(keyj.values())[0]
ctxj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ctx.json')))
PID, BID = ctxj['pid'], ctxj['bid']
S3 = 'br-wandering-field-w2ob6mpn.storage.c-1.us-east-2.aws.neon.build'

def req(host, method, path, body=None, headers=None):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if headers:
            h.update(headers)
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read()
        st = r.status
        conn.close()
        return st, raw.decode('utf-8', 'replace')
    except Exception as e:
        return -1, 'EXC %s' % e

cb = {'Authorization': 'Bearer ' + str(KEY), 'X-Bug-Bounty': 'xxbo'}
print('=== [1] issue storage:read 凭据 ===')
st, raw = req(API_HOST, 'POST', API_BASE + '/projects/%s/branches/%s/credentials' % (PID, BID),
              {'name': 'm8s3-%d' % (time.time() % 1000), 'scopes': ['storage:read'], 'principal_type': 'user'},
              headers=cb)
print('%d %s' % (st, raw[:400]))
try:
    j = json.loads(raw)
    TID = j.get('token_id', '')
    ACCESS = j.get('token_id', '')          # token_id = AWS_ACCESS_KEY_ID
    SECRET = j.get('s3_secret_access_key', '')
except Exception:
    TID = ACCESS = SECRET = ''
print('token_id:', TID[:20], 'secret 前8:', SECRET[:8])

if ACCESS and SECRET:
    print('\n=== [2] boto3 SigV4 请求 ===')
    try:
        import boto3
        from botocore.config import Config
        s3c = boto3.client('s3', endpoint_url='https://' + S3, region_name='us-east-2',
                           aws_access_key_id=ACCESS, aws_secret_access_key=SECRET,
                           config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4',
                                         retries={'max_attempts': 0}), verify=True)
        # ListBuckets
        try:
            r = s3c.list_buckets()
            print('[ListBuckets] OK %s' % json.dumps({b['Name'] for b in r.get('Buckets', [])})[:200])
        except Exception as e:
            print('[ListBuckets] ERR %s' % str(e)[:300])
        # ListObjects(根路径 bucket=branch?)
        try:
            r = s3c.list_objects_v2(Bucket=BID)
            print('[ListObjects %s] OK keys=%s' % (BID, [o['Key'] for o in r.get('Contents', [])])[:200])
        except Exception as e:
            print('[ListObjects] ERR %s' % str(e)[:300])
        # GetObject 任意 key(不存在判定)
        try:
            r = s3c.get_object(Bucket=BID, Key='nonexist-key-probe')
            print('[GetObject] OK(?!): %s' % str(r)[:200])
        except Exception as e:
            print('[GetObject] ERR %s' % str(e)[:300])
    except ImportError as e:
        print('boto3 导入失败:', e)

print('\n=== [3] cleanup: revoke ===')
if TID:
    st, raw = req(API_HOST, 'DELETE', API_BASE + '/projects/%s/branches/%s/credentials/%s' % (PID, BID, TID), headers=cb)
    print('revoke -> %d %s' % (st, raw[:100]))
