# -*- coding: utf-8 -*-
"""W5d: batch GET recon on never-tested console surfaces (read-only)."""
import json, ssl, http.client, time

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
PB = "damp-term-63384673"
PBMAIN = "br-raspy-band-w247957z"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

ctx = ssl.create_default_context()

def api(method, path, body=None, host=API_HOST, base=API_BASE, key=APIKEY):
    conn = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    hdr = {"X-Bug-Bounty": "xxbo", "Authorization": "Bearer " + key}
    if body is not None:
        hdr["Content-Type"] = "application/json"
        body = json.dumps(body)
    conn.request(method, base + path, body=body, headers=hdr)
    r = conn.getresponse()
    data = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, data[:500]

# GET probes on PA (and PB where interesting)
probes = [
    ("/projects/shared", PA),
    ("/projects/%s/members" % PA, PA),
    ("/projects/%s/permissions" % PA, PA),
    ("/projects/%s/branches/%s/credentials" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/ai_gateway" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/storage" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/logs/fields" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/masking_rules" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/backup_schedule" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/custom-domains" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/functions" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/buckets" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/auth" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/auth/email_and_password" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/auth/allow_localhost" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/auth/email_provider" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/auth/webhooks" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/auth/oauth_providers" % (PA, PAMAIN), PA),
    ("/projects/%s/branches/%s/auth/domains" % (PA, PAMAIN), PA),
    ("/projects/%s/snapshots" % PA, PA),
    ("/projects/%s/auth/integrations" % PA, PA),
    ("/projects/%s/auth/domains" % PA, PA),
    ("/projects/%s/auth/email_server" % PA, PA),
    ("/projects/%s/auth/oauth_providers" % PA, PA),
    ("/projects/%s/jwks" % PA, PA),
    ("/projects/%s/operations" % PA, PA),
    ("/consumption_history/projects", PA),
    ("/consumption_history/v2/projects", PA),
    ("/consumption_history/v2/branches", PA),
    ("/auth", PA),
    ("/projects/%s/advisors" % PA, PA),
    ("/projects/%s/available_preload_libraries" % PA, PA),
    # PB extras: data-api enabled? snapshots? credentials?
    ("/projects/%s/branches/%s/credentials" % (PB, PBMAIN), PB),
    ("/projects/%s/branches/%s/auth" % (PB, PBMAIN), PB),
    ("/projects/%s/branches/%s/storage" % (PB, PBMAIN), PB),
    ("/projects/%s/branches/%s/buckets" % (PB, PBMAIN), PB),
    ("/projects/%s/branches/%s/functions" % (PB, PBMAIN), PB),
    ("/projects/%s/snapshots" % PB, PB),
]

for path, tag in probes:
    try:
        st, data = api("GET", path)
        print("[%s] %d %s" % (tag, st, data[:280].replace("\n", " ")))
    except Exception as e:
        print("[%s] ERR %s %s" % (tag, path, e))
    time.sleep(0.4)
