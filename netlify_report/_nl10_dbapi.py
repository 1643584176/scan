# -*- coding: utf-8 -*-
"""NL10: database endpoint variants to see why 400 (param/route change?)"""
import http.client, ssl, sys
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'

variants = [
    "/api/v1/sites/%s/database?role=netlifydb_owner",
    "/api/v1/sites/%s/database",
    "/api/v1/sites/%s/database?role=owner",
    "/api/v1/sites/%s/databases",
    "/api/v1/sites/%s/database/branches",
    "/api/v1/accounts/libobo01/sites",
]
for v in variants:
    conn = http.client.HTTPSConnection("api.netlify.com", timeout=25, context=ctx)
    p = v % SITE_B if "%s" in v else v
    conn.request("GET", p, headers={"Authorization": "Bearer " + TOKEN_B,
                                    "User-Agent": "Mozilla/5.0 Chrome/126.0"})
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    print("%s\n  -> %d %s" % (p, r.status, raw[:400]), flush=True)
print("done")
