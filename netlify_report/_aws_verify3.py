# -*- coding: utf-8 -*-
import boto3, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from botocore.config import Config

def chk(p):
    aws = json.load(open(p, encoding='utf-8'))
    cfg = Config(region_name=aws.get('region', 'us-east-2'), retries={'max_attempts': 1}, connect_timeout=8, read_timeout=10)
    c = boto3.client('sts', aws_access_key_id=aws['access_key'],
                     aws_secret_access_key=aws['secret_key'],
                     aws_session_token=aws.get('session_token'), config=cfg)
    try:
        r = c.get_caller_identity()
        print(p.split('\\')[-1], '->', r['Arn'], '| account', r['Account'])
        return True
    except Exception as e:
        print(p.split('\\')[-1], 'ERR:', type(e).__name__, str(e)[:140])
        return False

chk(r'D:\scan\netlify_report\_aws_creds3.json')
