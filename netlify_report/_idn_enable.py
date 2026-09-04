# -*- coding: utf-8 -*-
# _idn_enable.py - POST /sites/{id}/identity to enable Netlify Identity on SITE_A
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

def req(method, url, body=None, tok=None, ct='application/json'):
    hdrs = {'Authorization': 'Bearer ' + tok}
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        return resp.status, resp.headers.get('content-type',''), resp.read(1500).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(1500).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:200]

base = 'https://api.netlify.com/api/v1/sites/%s/identity' % SITE_A
for body in (None, {}, {'site_id': SITE_A}):
    st, ct, b = req('POST', base, body, tok=TOKEN_A)
    print('POST %s body=%s -> %s %s' % (base, body, st, ct))
    print('   %s' % b[:600].replace('\n', ' '))
