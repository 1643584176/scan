# -*- coding: utf-8 -*-
"""一次性:创建私有 repo(env GHTOKEN),输出名字到 /tmp/nl_priv_repo.txt"""
import json, os, time, urllib.request

tok = os.environ['GHTOKEN']
name = 'nl-probe-%d' % int(time.time())
print('REPO_NAME=%s' % name)

req = urllib.request.Request(
    'https://api.github.com/user/repos',
    data=json.dumps({'name': name, 'private': True,
                     'description': 'temp idor probe', 'auto_init': False}).encode(),
    headers={'Authorization': 'token ' + tok, 'Accept': 'application/vnd.github+json',
             'User-Agent': 'probe'}, method='POST')
try:
    r = urllib.request.urlopen(req, timeout=20)
    print('create:', r.status)
    print(r.read()[:400])
    open(r'D:\scan\netlify_report\_priv_repo.txt', 'w').write(name)
except Exception as e:
    print('ERR', e)
    try:
        print(e.read()[:400])
    except Exception:
        pass
