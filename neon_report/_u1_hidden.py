# -*- coding: utf-8 -*-
"""Probe hidden console endpoints (present in JS, absent from OpenAPI v2 index).
Method: GET -> 200/400/403 = route exists; 404 = absent.
Then POST {} for write candidates -> 400/403/405 = exists.
"""
import json
import time
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
EP = "ep-crimson-fog-w2gucld1"
ORG = "org-flat-dawn-91601224"
LOG = r"F:\scan\neon_report\_u1_out.jsonl"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": (out or "")[:400]}
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-52s -> %s %s" % (rec["t"], key, st, note), flush=True)
    if isinstance(st, int) and 400 <= st < 600:
        try:
            e = json.loads(out)
            print("        code=%s msg=%s" % (e.get("code"), e.get("message", "")[:150]),
                  flush=True)
        except Exception:
            pass


def call(method, path, body=None, timeout=25):
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
    payload = json.dumps(body) if body is not None else None
    hdrs = dict(HB, Authorization="Bearer " + APIKEY)
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    conn.request(method, API_BASE + path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, data


GETS = [
    ("project query", "/projects/%s/query" % PA),
    ("project query/history", "/projects/%s/query/history" % PA),
    ("project saved_queries", "/projects/%s/saved_queries" % PA),
    ("project running_operations", "/projects/%s/running_operations" % PA),
    ("project branch_import", "/projects/%s/branch_import" % PA),
    ("project platform-served", "/projects/%s/platform-served" % PA),
    ("project notifications", "/projects/%s/notifications" % PA),
    ("project limits", "/projects/%s/limits" % PA),
    ("project applications/vercel", "/projects/%s/applications/vercel" % PA),
    ("project applications/vercel/branches", "/projects/%s/applications/vercel/branches" % PA),
    ("project applications/vercel/settings", "/projects/%s/applications/vercel/settings" % PA),
    ("project applications/vercel/vars", "/projects/%s/applications/vercel/vars" % PA),
    ("project applications/github", "/projects/%s/applications/github" % PA),
    ("project integrations/monitoring", "/projects/%s/integrations/monitoring" % PA),
    ("project integrations/monitoring/datadog", "/projects/%s/integrations/monitoring/datadog" % PA),
    ("project integrations/monitoring/debug", "/projects/%s/integrations/monitoring/debug" % PA),
    ("project integrations/monitoring/otel", "/projects/%s/integrations/monitoring/opentelemetry" % PA),
    ("project integrations/vercel", "/projects/%s/integrations/vercel" % PA),
    ("project auth/init", "/projects/%s/auth/init" % PA),
    ("project auth/sync_keys_vercel", "/projects/%s/auth/sync_keys_vercel" % PA),
    ("branch reset", "/projects/%s/branches/%s/reset" % (PA, PAMAIN)),
    ("branch reset_to_parent", "/projects/%s/branches/%s/reset_to_parent" % (PA, PAMAIN)),
    ("branch recover", "/projects/%s/branches/%s/recover" % (PA, PAMAIN)),
    ("branch consumption", "/projects/%s/branches/%s/consumption" % (PA, PAMAIN)),
    ("endpoint passwordless_auth", "/projects/%s/endpoints/%s/passwordless_auth" % (PA, EP)),
    ("endpoint stats", "/projects/%s/endpoints/%s/stats" % (PA, EP)),
    ("org billing/account", "/organizations/%s/billing/account" % ORG),
    ("org billing/invoices", "/organizations/%s/billing/invoices" % ORG),
    ("org billing/aigw purchase", "/organizations/%s/billing/aigw_credits/purchase" % ORG),
    ("org consumption", "/organizations/%s/consumption" % ORG),
    ("org deletion_checklist", "/organizations/%s/deletion_checklist" % ORG),
    ("org domains", "/organizations/%s/domains" % ORG),
    ("org early_access", "/organizations/%s/early_access" % ORG),
    ("org feature_flags", "/organizations/%s/feature_flags" % ORG),
    ("org features/enable", "/organizations/%s/features/enable" % ORG),
    ("org guests", "/organizations/%s/guests" % ORG),
    ("org limits", "/organizations/%s/limits" % ORG),
    ("org sso", "/organizations/%s/sso" % ORG),
    ("org sso/enforcement", "/organizations/%s/sso/enforcement" % ORG),
    ("user billing/account", "/billing/account"),
    ("user billing/invoices", "/billing/invoices"),
]

for key, path in GETS:
    st, out = call("GET", path)
    log("G " + key, st, out)
    time.sleep(0.3)
