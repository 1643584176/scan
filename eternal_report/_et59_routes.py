# -*- coding: utf-8 -*-
"""ET59: extract all webroutes/webapi/gw paths from z_main + no-session reachability triage"""
import re, os, ssl, http.client, time

D = os.path.dirname(os.path.abspath(__file__))
data = open(os.path.join(D, "_js", "z_main-8efa4cf644fa76389041.js"), "r", encoding="utf-8", errors="replace").read()

paths = set()
for m in re.finditer(r'"(/(?:webroutes|webapi|gw)/[a-zA-Z0-9/_.-]+)"', data):
    paths.add(m.group(1))
print("== extracted %d unique paths ==" % len(paths), flush=True)
for p in sorted(paths):
    print("  " + p, flush=True)

# pick query-ish GET candidates (no obvious write verbs)
WRITEY = ("delete", "update", "add", "create", "save", "edit", "remove", "cancel", "submit", "make", "post", "vote", "verify", "init")
cands = [p for p in sorted(paths) if not any(w in p.lower() for w in WRITEY)]
print("\n== probing %d read-like candidates (no params) ==" % len(cands), flush=True)

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

def get(path):
    try:
        conn = http.client.HTTPSConnection("www.zomato.com", 443, timeout=12, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "application/json,*/*",
                     "X-Hackerone": "xxbo", "Referer": "https://www.zomato.com/ncr/restaurants?q=pizza"})
        r = conn.getresponse()
        raw = r.read(4000)
        conn.close()
        body = raw.decode("utf-8", "replace")[:150].replace("\n", " ")
        print("[%d] %-58s %s" % (r.status, path[:58], body), flush=True)
    except Exception as e:
        print("[EXC] %-58s %s" % (path[:58], repr(e)[:80]), flush=True)

for p in cands[:24]:
    get(p)
    time.sleep(0.8)
print("done", flush=True)
