# -*- coding: utf-8 -*-
# _idn_cfgpatch.py - try PATCH/PUT instance config autoconfirm (reversible), then signup to get token
import json, urllib.request, urllib.error
from _net_creds import TOKEN_A, SITE_A

INST = '6a97f260e3e0091b16d132ce'

def req(method, url, body=None, tok=None, ct='application/json'):
    hdrs = {'Authorization': 'Bearer ' + tok}
    data = None
    if body is not None:
        hdrs['Content-Type'] = ct
        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body.encode()
    r = urllib.request.Request(url, method=method, headers=hdrs, data=data)
    try:
        resp = urllib.request.urlopen(r, timeout=25)
        return resp.status, resp.headers.get('content-type',''), resp.read(4000).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(4000).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:200]

base = 'https://api.netlify.com/api/v1/sites/%s/identity/%s' % (SITE_A, INST)
print('=== PATCH variants ===')
variants = [
    {'config': {'mailer': {'autoconfirm': True}}},
    {'config': {'config': {'mailer': {'autoconfirm': True}}}},
    {'disable_signup': False},
]
for bd in variants:
    st, ct, b = req('PATCH', base, bd, tok=TOKEN_A)
    print('PATCH body=%s' % json.dumps(bd)[:100])
    print('  -> %s %s' % (st, b[:900].replace('\n', ' ')))
    if st in (200, 201):
        # show autoconfirm value in response
        try:
            j = json.loads(b)
            print('  autoconfirm now =', j.get('config', {}).get('config', {}).get('mailer', {}).get('autoconfirm'))
        except Exception:
            pass
