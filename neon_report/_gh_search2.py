# -*- coding: utf-8 -*-
"""Global GitHub search: any public writeup/issue about Neon anonymized-branch bypass."""
import json
import ssl
import urllib.request
import urllib.parse

QUERIES = [
    '"cannot restore anonymized branches"',
    '"restricted_actions" neon anonymized',
    'neon anonymized branch fork original data',
    'neon data anonymization fork bypass',
]

ctx = ssl.create_default_context()
for q in QUERIES:
    url = "https://api.github.com/search/issues?q=" + urllib.parse.quote(q) + "&per_page=10"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "research"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            d = json.loads(r.read().decode())
        print("=== %s -> total %s" % (q, d.get("total_count")))
        for it in d.get("items", []):
            print("  #%s [%s] %s | %s" % (it.get("number"), it.get("state"),
                                          it.get("title", "")[:90], it.get("html_url")))
    except Exception as e:
        print("=== %s -> ERR %s" % (q, e))

# also code search needs auth; skip. repo search on other neon mirrors:
for repo in ("neondatabase/cloud", "neondatabase/neon-sdk-go"):
    url = "https://api.github.com/search/issues?q=" + urllib.parse.quote(
        "repo:%s anonymized" % repo) + "&per_page=10"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "research"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            d = json.loads(r.read().decode())
        print("=== %s -> total %s" % (repo, d.get("total_count")))
        for it in d.get("items", []):
            print("  #%s [%s] %s | %s" % (it.get("number"), it.get("state"),
                                          it.get("title", "")[:90], it.get("html_url")))
    except Exception as e:
        print("=== %s -> ERR %s" % (repo, e))
