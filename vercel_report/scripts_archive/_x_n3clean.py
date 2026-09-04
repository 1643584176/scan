# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api("DELETE", "/v2/sandboxes/n3?teamId=%s&projectId=%s" % (TEAM, PROJ), None, 30)
print("n3 delete:", c, r[:120])
c, r = api("GET", "/v2/sandboxes?teamId=%s" % TEAM, None, 30)
sb = json.loads(r).get('sandboxes', [])
run = [s['name'] for s in sb if s.get('status') == 'running']
print("running:", run)
