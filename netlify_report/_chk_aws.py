try:
    import boto3
    print('boto3 ok')
except Exception as e:
    print('boto3 missing:', e)
import shutil
print('aws cli:', shutil.which('aws'))
