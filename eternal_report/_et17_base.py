# -*- coding: utf-8 -*-
"""ET17: find base URL var definitions in zomato main bundle"""
import os, re

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
data = open(os.path.join(d, "z_main-8efa4cf644fa76389041.js"), encoding="utf-8", errors="replace").read()

# find assignments like var i="https://..." or i="..." etc. near concat defs
pat = re.compile(r'(?:var |,|;|\(|{)\s*([a-z])="(https?://[^"]+)"', re.I)
seen = {}
for m in pat.finditer(data):
    seen.setdefault(m.group(1), set()).add(m.group(2))
for k in sorted(seen):
    print("var %s -> %s" % (k, sorted(seen[k])[:6]))

print("\n== search domain 'i' usage ==")
# context where searchapi.php is CALLED with params (not just declared)
for m in re.finditer(r'An\s*\(', data):
    s = max(0, m.start() - 100)
    print("CALL:", data[s:m.end() + 350].replace("\n", " ")[:500], "\n---")
print("done", flush=True)
