# -*- coding: utf-8 -*-
"""curl 方式 deploy kf1 + 轮询状态(绕开 python multipart 问题)"""
import http.client, ssl, json, sys, time, subprocess
sys.path.insert(0, r'D:\scan\neon_report')
ctx = ssl.create_default_context()
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
SLUG = 'kf1'

# 1. curl deploy(multipart)
cmd = ['curl.exe', '-s', '-X', 'POST',
       'https://console-stage.neon.build/api/v2/projects/%s/branches/%s/functions/%s/deployments' % (P, B, SLUG),
       '-H', 'Authorization: Bearer %s' % key, '-H', 'X-Bug-Bounty: xxbo',
       '-F', 'zip=@D:\\scan\\neon_report\\_f1.zip', '-F', 'runtime=nodejs24']
r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
print('curl deploy ->', r.returncode)
print('stdout:', r.stdout[:500])
print('stderr:', r.stderr[:300])

# 2. 轮询 function 状态
def req(method, path):
    h = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
         'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key,
         'X-Bug-Bounty': 'xxbo'}
    conn = http.client.HTTPSConnection('console-stage.neon.build', context=ctx, timeout=30)
    conn.request(method, '/api/v2' + path, headers=h)
    r2 = conn.getresponse(); raw = r2.read(); st = r2.status; conn.close()
    return st, raw

for i in range(24):
    st, raw = req('GET', '/projects/%s/branches/%s/functions/%s' % (P, B, SLUG))
    if st == 200:
        try:
            fn = json.loads(raw).get('function', {})
            cur = fn.get('current_deployment', {})
            print('state: %s' % cur.get('status'))
            if cur.get('status') in ('completed', 'failed'):
                print('invocation_url:', fn.get('invocation_url'))
                print('fn json:', json.dumps(fn, indent=1)[:1800])
                break
        except Exception as e:
            print('parse err', e, raw[:200])
    else:
        print('get ->', st, raw[:200])
    time.sleep(5)
