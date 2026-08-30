# -*- coding: utf-8 -*-
"""复现 _x_pty2.py 的 main 逻辑"""
import base64, json, socket, ssl, struct, sys, time, urllib.request, urllib.error, re
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'ws46h'

print('STEP1: delete', flush=True)
c, r = api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
print('STEP2: deleted', c, flush=True)
time.sleep(3)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
print('STEP3: created', c, flush=True)
if c != 200:
    sys.exit(1)
print('DONE', flush=True)
