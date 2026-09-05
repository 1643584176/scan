# -*- coding: utf-8 -*-
"""GitHub issue search: any public reference to Neon anonymized-branch issues."""
import json
import ssl
import urllib.request
import urllib.parse

QUERIES = [
    "repo:neondatabase/neon anonymized",
    "repo:neondatabase/neon restricted_actions",
    "repo:neondatabase/neon branch anonymized fork",
    "repo:neondatabase/neon anonymize masking rules original data",
]

ctx = ssl.create_default_context()
for q in QUERIES:
    url = "https://api.github.com/search/issues?q=" + urllib.parse.quote(q) + "&per_page=15"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "research"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            d = json.loads(r.read().decode())
        print("=== %s -> total %s" % (q, d.get("total_count")))
        for it in d.get("items", []):
            print("  #%s [%s] %s" % (it.get("number"), it.get("state"), it.get("title", "")[:110]))
            print("     ", it.get("html_url"))
    except Exception as e:
        print("=== %s -> ERR %s" % (q, e))
