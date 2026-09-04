# -*- coding: utf-8 -*-
import json, sys
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
from vercel_driver import api, TEAM

c, r = api('GET', '/v13/deployments/dpl_6Hj6eEU9W4nVwnCCBd8ohEL4Qf8U?teamId=%s' % TEAM)
d = json.loads(r)
print('status:', d.get('status'), 'readyState:', d.get('readyState'))
print('aliasAssigned:', d.get('aliasAssigned'), 'aliases:', d.get('alias'))
print('url:', d.get('url'))
print('functions:', json.dumps(d.get('functions'))[:400])
print('regions:', d.get('regions'))
print('errorMessage:', d.get('errorMessage'))
# 查 alias 分配状态
c2, r2 = api('GET', '/v4/domains?teamId=%s&limit=50' % TEAM)
print('domains http:', c2, r2[:300])
