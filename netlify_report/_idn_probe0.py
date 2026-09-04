# -*- coding: utf-8 -*-
# _idn_probe0.py - probe Identity-related endpoints on SITE_A domain & api.netlify.com
# stage: discovery (what exists before enabling identity)
import json, urllib.request, urllib.error

SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
NAME = 'sec-test-rcf6lz'

def get(url, hdrs=None):
    req = urllib.request.Request(url, headers=hdrs or {})
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return r.status, r.headers.get('content-type',''), r.read(400).decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type',''), e.read(400).decode('utf-8','replace')
    except Exception as e:
        return 'ERR', '', str(e)[:200]

hosts = ['https://%s.netlify.app' % NAME, 'https://%s.netlify.app' % SITE_A, 'https://api.netlify.com']
paths = [
    '/.netlify/identity/settings',
    '/.netlify/identity/admin/users',
    '/.netlify/identity',
    '/.netlify/identity/health',
    '/api/v1/sites/%s/identity' % SITE_A,
    '/api/v1/sites/%s/identity-instances' % SITE_A,
    '/api/v1/sites/%s/identity/instances' % SITE_A,
]
for h in hosts:
    for p in paths:
        url = h + p
        st, ct, body = get(url)
        # skip expected 404 html noise but log anyway
        print('%-8s %-70s %s %s' % (st, url, ct, body[:120].replace('\n',' ')))
