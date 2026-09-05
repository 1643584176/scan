# -*- coding: utf-8 -*-
"""NL7: network retry on A/B site roots + API-side site url check"""
import http.client, ssl, sys, json
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_A

ctx = ssl.create_default_context()

for host in ("sec-test-rcf6lz.netlify.app", "sec-b-08v4pk.netlify.app"):
    for i in range(3):
        try:
            conn = http.client.HTTPSConnection(host, timeout=15, context=ctx)
            conn.request("GET", "/", headers={"User-Agent": "Mozilla/5.0 Chrome/126.0"})
            r = conn.getresponse()
            body = r.read(200)
            print("%s try%d -> %d server=%s ct=%s body=%s" % (host, i, r.status, r.getheader("Server", "?"),
                                                              r.getheader("Content-Type", "?")[:30],
                                                              body[:60].decode("utf-8", "replace")))
            conn.close()
        except Exception as e:
            print("%s try%d ERR %s" % (host, i, str(e)[:120]))
    # function path
    try:
        conn = http.client.HTTPSConnection(host, timeout=15, context=ctx)
        conn.request("GET", "/.netlify/functions/probe1", headers={"User-Agent": "Mozilla/5.0 Chrome/126.0"})
        r = conn.getresponse()
        body = r.read(120)
        print("%s fn probe1 -> %d %s" % (host, r.status, body[:80].decode("utf-8", "replace")))
        conn.close()
    except Exception as e:
        print("%s fn ERR %s" % (host, str(e)[:120]))

# API side: deploy function listing for site A
conn = http.client.HTTPSConnection("api.netlify.com", timeout=25, context=ctx)
conn.request("GET", "/api/v1/sites/04f08ff6-f274-47ac-b6d7-5fb1e055f3b4/deploys?per_page=10",
             headers={"Authorization": "Bearer " + TOKEN_A})
r = conn.getresponse()
d = json.loads(r.read().decode())
print("\nA deploys:")
for dep in d:
    print("  ", dep.get("id", "")[:12], dep.get("title"), dep.get("state"), "created:", dep.get("created_at", "")[:19],
          "fn:", list((dep.get("functions") or {}).keys()) if isinstance(dep.get("functions"), dict) else dep.get("function_count"))
conn.close()
print("done")
