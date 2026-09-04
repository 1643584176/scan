# -*- coding: utf-8 -*-
import boto3, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from botocore.config import Config

def load(p):
    return json.load(open(p, encoding='utf-8'))

def mk(aws, region='us-east-2'):
    cfg = Config(region_name=region, retries={'max_attempts': 1}, connect_timeout=8, read_timeout=10)
    return boto3.client('sts', aws_access_key_id=aws['access_key'],
                        aws_secret_access_key=aws['secret_key'],
                        aws_session_token=aws.get('session_token'), config=cfg)

for name, p in [('A-creds', r'D:\scan\netlify_report\_aws_creds1.json'),
                ('B-creds', r'D:\scan\netlify_report\_aws_creds2.json')]:
    try:
        aws = load(p)
        r = mk(aws).get_caller_identity()
        print(name, '->', r['Arn'], '| account', r['Account'])
    except Exception as e:
        print(name, 'ERR:', type(e).__name__, str(e)[:160])
