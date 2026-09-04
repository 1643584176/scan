# -*- coding: utf-8 -*-
"""S3 SigV4 细节: ClientError response + region 变体(us-east-2 vs us-east-1)"""
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
st, raw = req(API_HOST, 'POST', API_BASE + '/projects/%s/branches/%s/credentials' % (PID, BID),
              {'name': 'm8s3b-%d' % (time.time() % 1000), 'scopes': ['storage:read'], 'principal_type': 'user'},
              headers=cb)
j = json.loads(raw)
TID, SECRET = j.get('token_id', ''), j.get('s3_secret_access_key', '')

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

for region in ('us-east-2', 'us-east-1'):
    print('\n=== region=%s ===' % region)
    s3c = boto3.client('s3', endpoint_url='https://' + S3, region_name=region,
                       aws_access_key_id=TID, aws_secret_access_key=SECRET,
                       config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4',
                                     retries={'max_attempts': 0}), verify=True)
    for opname, fn in [('list_buckets', lambda: s3c.list_buckets()),
                       ('list_objects', lambda: s3c.list_objects_v2(Bucket=BID))]:
        try:
            r = fn()
            print('[%s] OK %s' % (opname, str(r)[:200]))
        except ClientError as e:
            resp = e.response
            print('[%s] ClientError status=%s code=%s body=%s' % (
                opname,
                resp.get('ResponseMetadata', {}).get('HTTPStatusCode'),
                resp.get('Error', {}).get('Code'),
                str(resp.get('Error', {}))[:250]))
        except Exception as e:
            print('[%s] ERR %s' % (opname, str(e)[:250]))

st, raw = req(API_HOST, 'DELETE', API_BASE + '/projects/%s/branches/%s/credentials/%s' % (PID, BID, TID), headers=cb)
print('\ncleanup revoke -> %d' % st)
