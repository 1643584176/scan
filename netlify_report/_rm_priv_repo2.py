# -*- coding: utf-8 -*-
"""重试删除私有 repo(env GHTOKEN),名字固定"""
import os, urllib.request

tok = os.environ['GHTOKEN']
name = 'nl-probe-1788336328'
req = urllib.request.Request('https://api.github.com/repos/1643584176/' + name,
                             headers={'Authorization': 'token ' + tok, 'User-Agent': 'probe',
                                      'Accept': 'application/vnd.github+json'}, method='DELETE')
try:
    r = urllib.request.urlopen(req, timeout=20)
    print('delete:', r.status)
except Exception as e:
    print('ERR', e)
    try:
        print(e.read()[:300])
    except Exception:
        pass
