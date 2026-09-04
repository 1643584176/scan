# -*- coding: utf-8 -*-
# _idn_cfgcheck.py - GET instance config to verify autoconfirm change
import json, urllib.request
from _net_creds import TOKEN_A, SITE_A

req = urllib.request.Request(
    'https://api.netlify.com/api/v1/sites/%s/identity/6a97f260e3e0091b16d132ce' % SITE_A,
    headers={'Authorization': 'Bearer ' + TOKEN_A})
j = json.loads(urllib.request.urlopen(req).read())
cfg = j['config']['config']
print('autoconfirm:', cfg['mailer']['autoconfirm'])
print('disable_signup:', cfg.get('disable_signup'))
print('smtp.max_frequency:', cfg['smtp'].get('max_frequency'))
