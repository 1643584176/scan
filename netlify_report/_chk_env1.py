# -*- coding: utf-8 -*-
import sys
try:
    import boto3
    print('boto3 ok', boto3.__version__)
except Exception as e:
    print('boto3 missing:', e)
import os
for f in sorted(os.listdir('.')):
    if f.startswith('_net_aws'):
        print(f)
