# -*- coding: utf-8 -*-
import json
from vercel_driver import list_sandboxes

c, r = list_sandboxes()
d = json.loads(r)
for sb in d['sandboxes']:
    print(sb['name'], sb['currentSessionId'], sb['status'], sb.get('networkPolicy', {}).get('mode', '?'))
