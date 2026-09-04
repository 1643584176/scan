# -*- coding: utf-8 -*-
import os, urllib.request
req = urllib.request.Request('https://api.github.com/user',
                             headers={'Authorization': 'token ' + os.environ['GHTOKEN'],
                                      'User-Agent': 'p'})
r = urllib.request.urlopen(req)
print('scopes:', r.headers.get('x-oauth-scopes'))
print(r.read()[:150])
