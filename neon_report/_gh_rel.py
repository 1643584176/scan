# -*- coding: utf-8 -*-
"""Check neondatabase/neon release notes for anonym* mentions."""
import json
import ssl
import urllib.request

url = "https://api.github.com/repos/neondatabase/neon/releases?per_page=100"
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                           "User-Agent": "scan-audit"})
try:
    rels = json.loads(urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=40).read())
except Exception as e:
    print("ERR:", str(e)[:200])
    raise SystemExit
hits = 0
print("total releases fetched:", len(rels))
for r in rels:
    body = (r.get("body") or "") + " " + (r.get("name") or "")
    if "anonym" in body.lower():
        hits += 1
        print("RELEASE:", r.get("tag_name"), "|", (r.get("name") or "")[:80])
        print("   ", body[:600].replace("\n", " "))
print("releases mentioning anonym*: %d / %d" % (hits, len(rels)))
