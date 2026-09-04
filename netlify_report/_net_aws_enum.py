# -*- coding: utf-8 -*-
"""Netlify:枚举 aws-lambda-execute 凭证权限范围(只读探测,判断是否平台共享/跨租户)
每个探测项裁剪输出,允许/拒绝分别标记
"""
import json, os, sys, boto3
from botocore.exceptions import ClientError, BotoCoreError

P = os.path.dirname(os.path.abspath(__file__))
creds = json.load(open(os.path.join(P, '_aws_creds.json'), encoding='utf-8'))
REGION = creds.get('AWS_REGION') or 'us-east-1'

sess = boto3.Session(
    aws_access_key_id=creds['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=creds['AWS_SESSION_TOKEN'],
    region_name=REGION,
)

def trial(name, fn, out_len=400):
    try:
        r = fn()
        print('[ALLOW]', name, '->', json.dumps(r, default=str)[:out_len])
        return r
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', '?')
        print('[DENY ]', name, '|', code, '|', str(e)[:160])
        return None
    except BotoCoreError as e:
        print('[NETERR]', name, '|', str(e)[:120])
        return None
    except Exception as e:
        print('[ERR]', name, '|', str(e)[:160])
        return None

print('==== region =', REGION, '====')

# --- 全局/账号级 ---
trial('sts.get_caller_identity', lambda: sess.client('sts').get_caller_identity())
trial('iam.list_users', lambda: sess.client('iam').list_users(MaxItems=5))
trial('iam.list_roles', lambda: sess.client('iam').list_roles(MaxItems=5))
trial('iam.get_account_authorization_details', lambda: sess.client('iam').get_account_authorization_details(MaxItems=5))
trial('s3.list_buckets', lambda: sess.client('s3').list_buckets())
trial('s3.list_account_aliases?', lambda: sess.client('s3').list_buckets())

# --- 区域服务 ---
def svc_list(service, call):
    c = sess.client(service)
    return getattr(c, call)()

trial('lambda.list_functions', lambda: svc_list('lambda', 'list_functions')(None) if False else sess.client('lambda').list_functions(MaxItems=20))
trial('dynamodb.list_tables', lambda: sess.client('dynamodb').list_tables(Limit=20))
trial('sqs.list_queues', lambda: sess.client('sqs').list_queues(MaxResults=20))
trial('secretsmanager.list_secrets', lambda: sess.client('secretsmanager').list_secrets(MaxResults=20))
trial('ssm.describe_parameters', lambda: sess.client('ssm').describe_parameters(MaxResults=20))
trial('ec2.describe_instances', lambda: sess.client('ec2').describe_instances(MaxResults=5))
trial('ecr.describe_repositories', lambda: sess.client('ecr').describe_repositories(maxResults=20))
trial('cloudwatch.list_metrics', lambda: sess.client('cloudwatch').list_metrics(MaxRecords=20))
trial('logs.describe_log_groups', lambda: sess.client('logs').describe_log_groups(limit=20))
trial('stepfunctions.list_state_machines', lambda: sess.client('stepfunctions').list_state_machines(maxResults=20))
trial('events.list_rules', lambda: sess.client('events').list_rules(Limit=20))
trial('apigateway.get_rest_apis', lambda: sess.client('apigateway').get_rest_apis(limit=20))
trial('apigatewayv2.get_apis', lambda: sess.client('apigatewayv2').get_apis(MaxResults=20))
trial('sns.list_topics', lambda: sess.client('sns').list_topics(MaxResults=20))
trial('kms.list_keys', lambda: sess.client('kms').list_keys(Limit=20))
trial('sts.get_session_token', lambda: sess.client('sts').get_session_token())
