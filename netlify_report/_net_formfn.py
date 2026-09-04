# -*- coding: utf-8 -*-
"""Netlify:老式 form 函数测试(fetch-site 等)"""
import http.client, ssl, gzip, brotli, sys, json, urllib.parse
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_NET

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
ctx = ssl.create_default_context()

def req(path, method='POST', form=None, headers=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=25)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json'}
    body = None
    if form is not None:
        h['Content-Type'] = 'application/x-www-form-urlencoded'
        body = urllib.parse.urlencode(form).encode()
    if headers:
        h.update(headers)
    conn.request(method, path, body=body, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

tests = [
    ('/.netlify/functions/fetch-site', {'siteId': SITE_ID}),
    ('/.netlify/functions/fetch-site', {'site_id': SITE_ID}),
    ('/.netlify/functions/get-sites', {'accountId': '1643584176'}),
    ('/.netlify/functions/fetch-databases', {'siteId': SITE_ID}),
    ('/.netlify/functions/fetch-databases', {'site_id': SITE_ID}),
    ('/.netlify/functions/fetch-database-connection', {'siteId': SITE_ID, 'databaseId': 'x'}),
    ('/.netlify/functions/get-trial-info', {'teamId': '1643584176'}),
    ('/.netlify/functions/get-team-plan', {'teamId': '1643584176'}),
    ('/.netlify/functions/get-payment-customer', {'teamId': '1643584176'}),
    ('/.netlify/functions/generate-signed-url', {'path': '/test.txt', 'siteId': SITE_ID}),
    ('/.netlify/functions/validate-signed-url', {'url': 'x'}),
    ('/.netlify/functions/fetch-private-integrations', {'teamId': '1643584176'}),
    ('/.netlify/functions/fetch-integration', {'integrationSlug': 'x'}),
    ('/.netlify/functions/get-extension-config', {'teamId': '1643584176', 'extensionSlug': 'x'}),
    ('/.netlify/functions/fetch-integration-hub', {}),
    ('/.netlify/functions/event-observed', {}),
]
for p, form in tests:
    try:
        s, raw = req(p, form=form, headers={'Cookie': COOKIE_NET})
        body = raw[:160].decode('utf-8', 'ignore').replace('\n', ' ')
        print('%-52s %d %s' % (p + ' ' + str(form)[:30], s, body))
    except Exception as e:
        print('%-52s ERR %s' % (p, str(e)[:40]))
