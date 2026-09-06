# -*- coding: utf-8 -*-
import urllib.request
import urllib.error

for path in ['/', 'index.php?module=Login']:
    try:
        r = urllib.request.urlopen('http://127.0.0.1:8080/' + path, timeout=20)
        print(path, '->', r.status)
    except urllib.error.HTTPError as e:
        print(path, '-> HTTP', e.code)
    except Exception as e:
        print(path, '-> ERR', type(e).__name__, e)
