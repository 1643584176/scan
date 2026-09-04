# -*- coding: utf-8 -*-
"""Netlify:枚举新账户 169879185114 凭证权限(账户 B 函数运行时凭证)"""
import json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
import boto3
from botocore.config import Config

aws = json.load(open(r'D:\scan\netlify_report\_aws_creds2.json'))
cfg = Config(region_name=aws.get('region', 'us-east-2'), retries={'max_attempts': 1}, connect_timeout=8, read_timeout=8)

def mk(service):
    return boto3.client(service, aws_access_key_id=aws['access_key'],
                        aws_secret_access_key=aws['secret_key'],
                        aws_session_token=aws['session_token'],
                        config=cfg)

# 1. 身份
try:
    r = mk('sts').get_caller_identity()
    print('Identity:', r['Arn'], '| Account:', r['Account'])
except Exception as e:
    print('sts ERR:', type(e).__name__, str(e)[:200])

# 2. lambda 只读操作
print()
print('=== lambda ===')
for op, kw in [('list_functions', {}), ('get_function', {'FunctionName': aws.get('lambda_name', '')}),
               ('list_layers', {}), ('list_event_source_mappings', {}),
               ('list_aliases', {'FunctionName': aws.get('lambda_name', '')})]:
    try:
        r = getattr(mk('lambda'), op)(**kw)
        keys = list(r.keys())[:4]
        print('%s OK keys=%s' % (op, keys))
        if op == 'get_function':
            print('  ->', json.dumps(r.get('Configuration', {}))[:300])
    except Exception as e:
        msg = str(e)
        print('%s ERR: %s' % (op, msg[:180]))

# 3. s3 / iam / logs / secretsmanager / ssm
print()
print('=== s3 ===')
try:
    r = mk('s3').list_buckets()
    print('list_buckets OK:', [b['Name'] for b in r.get('Buckets', [])][:5])
except Exception as e:
    print('list_buckets ERR:', str(e)[:180])
print('=== iam ===')
for op in ['list_users', 'list_roles', 'list_policies']:
    try:
        r = getattr(mk('iam'), op)()
        print('%s OK' % op)
    except Exception as e:
        print('%s ERR: %s' % (op, str(e)[:150]))
print('=== logs ===')
try:
    r = mk('logs').describe_log_groups()
    print('describe_log_groups OK:', len(r.get('logGroups', [])))
except Exception as e:
    print('describe_log_groups ERR:', str(e)[:150])
print('=== secretsmanager ===')
try:
    r = mk('secretsmanager').list_secrets()
    print('list_secrets OK:', len(r.get('SecretList', [])))
except Exception as e:
    print('list_secrets ERR:', str(e)[:150])
print('=== ssm ===')
try:
    r = mk('ssm').describe_parameters()
    print('describe_parameters OK:', len(r.get('Parameters', [])))
except Exception as e:
    print('describe_parameters ERR:', str(e)[:150])
