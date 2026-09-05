# -*- coding: utf-8 -*-
"""Neon S6 mini: logs/query endpoint + per-project log isolation."""
import json
import time
import ssl
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
PB = "damp-term-63384673"
PBMAIN = "br-raspy-band-w247957z"
LOG = r"F:\scan\neon_report\_s6_out.jsonl"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": (out or "")[:1000]}
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-44s -> %s %s" % (rec["t"], key, st, note), flush=True)
    if isinstance(st, int) and 400 <= st < 600:
        try:
            e = json.loads(out)
            print("        code=%s msg=%s" % (e.get("code"), e.get("message", "")[:200]),
                  flush=True)
        except Exception:
            print("        raw:", (out or "")[:200], flush=True)


def call(method, path, body=None, timeout=30):
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


def main():
    # per-project log field isolation
    for tag, pid, bid in (("PA", PA, PAMAIN), ("PB", PB, PBMAIN)):
        st, out = call("GET", "/projects/%s/branches/%s/logs/fields" % (pid, bid))
        log("logs fields %s" % tag, st, out[:400])
        st, out = call("POST", "/projects/%s/branches/%s/logs/query" % (pid, bid),
                       {"query": "service_name = 'console'", "limit": 5})
        log("logs query %s" % tag, st, out[:600])
    # cross-project: PA path + PB branch
    st, out = call("GET", "/projects/%s/branches/%s/logs/fields" % (PA, PBMAIN))
    log("logs fields path(PA)+PB branch", st, out[:300])
    st, out = call("POST", "/projects/%s/branches/%s/logs/query" % (PA, PBMAIN),
                   {"query": "service_name = 'console'", "limit": 5})
    log("logs query path(PA)+PB branch", st, out[:300])
    print("== DONE", flush=True)


if __name__ == "__main__":
    main()
