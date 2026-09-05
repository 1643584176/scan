# -*- coding: utf-8 -*-
"""V32: console-stage v2 management surface enumeration (beyond projects/branches/endpoints/roles)
each: GET -> status class; 2xx/4xx get followed up, 404 = route absent"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
APIKEY = json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]
PROJ = "orange-sun-90493739"
BR = "br-wandering-field-w2ob6mpn"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def api(method, path, body=None):
    if path.startswith("GET "):
        method, path = "GET", path[4:]
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=25, context=ctx)
    h = {"Content-Type": "application/json", "X-Bug-Bounty": "xxbo",
         "Authorization": "Bearer " + APIKEY, "User-Agent": "Mozilla/5.0"}
    conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse()
    d = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, d


def main():
    out("== V32 console v2 surface ==")
    paths = [
        # account/org level
        ("api_keys", "/api_keys"),
        ("members", "/members"),
        ("invites", "/invites"),
        ("organizations", "/organizations"),
        ("accounts", "/accounts"),
        ("user", "/user"),
        ("consumption", "/consumption"),
        ("settings", "/settings"),
        ("audit", "/audit/events"),
        ("billing", "/billing"),
        ("plans", "/plans"),
        ("payment_methods", "/payment_methods"),
        ("notifications", "/notifications"),
        ("webhooks", "/webhooks"),
        # project level
        ("proj settings", "GET /projects/%s/settings" % PROJ),
        ("proj archive", "GET /projects/%s/archive" % PROJ),
        ("proj operations", "GET /projects/%s/operations" % PROJ),
        ("proj members", "GET /projects/%s/members" % PROJ),
        ("proj invites", "GET /projects/%s/invites" % PROJ),
        ("proj api_keys", "GET /projects/%s/api_keys" % PROJ),
        ("proj consumption", "GET /projects/%s/consumption" % PROJ),
        ("proj usage", "GET /projects/%s/usage" % PROJ),
        ("proj audit", "GET /projects/%s/audit_events" % PROJ),
        ("proj webhooks", "GET /projects/%s/webhooks" % PROJ),
        ("proj ip_allow", "GET /projects/%s/ip_allow" % PROJ),
        ("proj network", "GET /projects/%s/network_restrictions" % PROJ),
        ("proj databases", "GET /projects/%s/databases" % PROJ),
        ("proj roles", "GET /projects/%s/roles" % PROJ),
        ("proj endpoints", "GET /projects/%s/endpoints" % PROJ),
        ("proj snis", "GET /projects/%s/snis" % PROJ),
        ("proj custom_hostnames", "GET /projects/%s/custom_hostnames" % PROJ),
        ("proj compute", "GET /projects/%s/compute" % PROJ),
        ("proj branches/backups", "GET /projects/%s/branches/%s/backups" % (PROJ, BR)),
        ("proj branch data", "GET /projects/%s/branches/%s/data" % (PROJ, BR)),
        ("proj branch settings", "GET /projects/%s/branches/%s/settings" % (PROJ, BR)),
        ("proj branch api_keys", "GET /projects/%s/branches/%s/api_keys" % (PROJ, BR)),
        ("proj branch roles", "GET /projects/%s/branches/%s/roles" % (PROJ, BR)),
        ("proj branch databases", "GET /projects/%s/branches/%s/databases" % (PROJ, BR)),
        ("proj branch schema", "GET /projects/%s/branches/%s/schema" % (PROJ, BR)),
        ("proj branch inspect", "GET /projects/%s/branches/%s/inspect" % (PROJ, BR)),
        ("proj branch auth", "GET /projects/%s/branches/%s/auth" % (PROJ, BR)),
    ]
    hits = []
    for tag, p in paths:
        try:
            st, d = api("GET", p)
            mark = "  <<<" if st != 404 else ""
            out("%-28s -> %3d %s%s" % (tag, st, d[:60].replace("\n", " "), mark))
            if st != 404:
                hits.append((tag, p, st, d[:200]))
            time.sleep(0.15)
        except Exception as ex:
            out("%-28s -> ERR %s" % (tag, ex))
    out("\n== non-404 hits: %d ==" % len(hits))
    for tag, p, st, d in hits:
        out("  %-28s %s %s" % (tag, st, d[:150]))
    out("done")


if __name__ == "__main__":
    main()
