# -*- coding: utf-8 -*-
"""Network matrix: which data-plane entry points are reachable from staging?
1) fetch endpoint host from API
2) TCP+TLS probe: ep-* hosts, pg.neon.tech, pooler variants, auth domain
"""
import json
import time
import ssl
import socket
import http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
HB = {"X-Bug-Bounty": "xxbo"}
PA = "orange-sun-90493739"
LOG = r"F:\scan\neon_report\_u4_out.txt"

with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]


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


def out(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


# 1. endpoints + branches to get hosts
st, d = call("GET", "/projects/%s/endpoints" % PA)
out("== endpoints: %s" % st)
try:
    for ep in json.loads(d).get("endpoints", []):
        out("   id=%s host=%s type=%s state=%s" % (
            ep.get("id"), ep.get("host"), ep.get("type"), ep.get("state")))
except Exception:
    out("   raw: %s" % d[:500])


def tls_probe(host, port=5432, timeout=8, sni=None):
    """Return: (tcp_ok, tls_ok, banner)"""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
    except Exception as e:
        return False, False, "tcp fail: %s" % type(e).__name__
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        tls = ctx.wrap_socket(s, server_hostname=sni or host)
        # read startup banner (pg sends 'N' error or SSL ok then wait)
        tls.settimeout(3)
        try:
            data = tls.recv(64)
            return True, True, "tls ok, recv=%r" % data[:40]
        except Exception as e:
            return True, True, "tls ok, recv err %s" % type(e).__name__
    except Exception as e:
        try:
            s.close()
        except Exception:
            pass
        return True, False, "tls fail: %s" % type(e).__name__


# 2. probe matrix
hosts = [
    "ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build",
    "ep-crimson-fog-w2gucld1.us-east-2.aws.stage.neon.build",
    "ep-crimson-fog-w2gucld1.neon.build",
    "pg.neon.tech",
    "pg.stage.neon.build",
    "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build",
    "console-stage.neon.build",
]
for h in hosts:
    tcp, tls, note = tls_probe(h)
    out("%-70s tcp=%s tls=%s %s" % (h, tcp, tls, note))
    time.sleep(0.3)

# DNS level check
out("")
for h in hosts:
    try:
        infos = socket.getaddrinfo(h, 5432, socket.AF_UNSPEC, socket.SOCK_STREAM)
        out("%-70s -> %s" % (h, sorted(set(i[4][0] for i in infos))[:4]))
    except Exception as e:
        out("%-70s -> DNS FAIL %s" % (h, e))
print("== DONE", flush=True)
