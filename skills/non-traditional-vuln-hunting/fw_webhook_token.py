# -*- coding: utf-8 -*-
"""创建 webhook.site 捕获端 token"""
import json, urllib.request

req = urllib.request.Request("https://webhook.site/token", method="POST")
req.add_header("Accept", "application/json")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=15) as r:
    d = json.loads(r.read().decode())
print(json.dumps(d, indent=2)[:500])
