# -*- coding: utf-8 -*-
"""只读:GET data-api settings 全量(找 origins/trustedOrigins 键)"""
import json, http.client, ssl, sys

sys.path.insert(0, '.')
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

ctx = ssl.create_default_context()
P = 'orange-sun-90493739'
B = 'br-wandering-field-w2ob6mpn'
key = json.load(open('_apikey.json', encoding='utf-8'))['key']

conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=20)
h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json',
     'Authorization': 'Bearer ' + key}
h.update(HEADERS_TEST)
conn.request('GET', API_BASE + '/projects/%s/branches/%s/data-api/neondb' % (P, B), headers=h)
r = conn.getresponse(); raw = r.read(); st = r.status; conn.close()
print('->', st)
print(raw.decode(errors='replace')[:4000])
