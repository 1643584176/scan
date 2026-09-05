# -*- coding: utf-8 -*-
"""GitHub search #3: commits + releases mentioning anonymized-branch security fixes.
If Neon fixed a fork/restore gap internally, the commit text may surface in the public
repo (console is closed, but control-plane hints / release notes may appear).
"""
import json
import ssl
import urllib.request

Q = [
    "repo:neondatabase/neon anonymized branch fork",
    "repo:neondatabase/neon restricted_actions anonymized",
    '"cannot restore anonymized branches"',
    "repo:neondatabase/neon anonymization fork raw",
]

for q in Q:
    url = "https://api.github.com/search/issues?q=" + urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                   "User-Agent": "scan-audit"})
        d = json.loads(urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=30).read())
        print("Q:", q, "| total:", d.get("total_count"))
        for it in d.get("items", [])[:5]:
            print("   -", it.get("title", "")[:120], "|", it.get("html_url", ""))
    except Exception as e:
        print("Q:", q, "| ERR:", str(e)[:150])

# also check release notes mentions
try:
    url = "https://api.github.com/repos/neondatabase/neon/releases?per_page=100"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "scan-audit"})
    rels = json.loads(urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=30).read())
    hits = 0
    for r in rels:
        body = (r.get("body") or "") + " " + (r.get("name") or "")
        if "anonym" in body.lower():
            hits += 1
            print("RELEASE:", r.get("tag_name"), "|", r.get("name"), "|", body[:400].replace("\n", " "))
    print("releases mentioning anonym*: %d / %d" % (hits, len(rels)))
except Exception as e:
    print("releases ERR:", str(e)[:150])
print("== DONE")
