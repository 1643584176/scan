# -*- coding: utf-8 -*-
"""Single raw tracker request w/ verbose result."""
import urllib.error
import urllib.parse
import urllib.request

p = {'idsite': 1, 'rec': '1', 'url': 'http://127.0.0.1:8080/home',
     'action_name': 'Home', '_id': 'aabbccddeeff0011', 'rand': '12345678'}
data = urllib.parse.urlencode(p).encode()
req = urllib.request.Request('http://127.0.0.1:8080/matomo.php', data=data)
req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0')
try:
    r = urllib.request.urlopen(req, timeout=45)
    print('status', r.status)
    print('body', r.read().decode('utf-8', 'replace')[:200])
    print('hdrs', dict(r.headers))
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode('utf-8', 'replace')[:300])
except Exception as e:
    print('ERR', type(e).__name__, str(e)[:300])
