# -*- coding: utf-8 -*-
p = r'F:\scan\netlify_report\_nl4_awsprobe.py'
s = open(p, encoding='utf-8').read()
s = s.replace("from _net_creds import TOKEN_B", "from _net_creds import TOKEN_A")
s = s.replace("SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'", "SITE_A = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'")
s = s.replace("token=TOKEN_B", "token=TOKEN_A")
s = s.replace("/api/v1/sites/%s/deploys/%s' % (SITE_B, DID)", "/api/v1/sites/%s/deploys/%s' % (SITE_A, DID)")
s = s.replace('sec-b-08v4pk.netlify.app', 'sec-test-rcf6lz.netlify.app')
open(p, 'w', encoding='utf-8').write(s)
print('patched', 'TOKEN_A' in s and 'SITE_A' in s and 'sec-test-rcf6lz' in s)
