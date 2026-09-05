# -*- coding: utf-8 -*-
"""V26e: verify real /token JWT against stored publicKey.
If verify passes but no usable seed in blob -> signing key lives server-side
(KMS/env), table privateKey is redundant/encrypted -> not exploitable."""
import json, ssl, time, http.client, base64

NA = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"
ctx = ssl.create_default_context()


def req(host, method, path, body=None, hdr=None, timeout=20):
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


def b64u(s):
    s = s.encode() if isinstance(s, str) else s
    return base64.b64encode(s).decode().replace("+", "-").replace("/", "_").rstrip("=")


def b64d(s):
    s2 = s.replace("-", "+").replace("_", "/")
    s2 += "=" * (-len(s2) % 4)
    return base64.b64decode(s2)


# 1. real JWT
st, raw, hd = req(NA, "POST", "/neondb/auth/sign-in/email",
                  {"email": "libobo1229+na_org1@gmail.com", "password": "SecTest!2026pass"},
                  {"Origin": "http://localhost:3000"})
ck = ""
for part in (hd.get("set-cookie") or "").split(","):
    kv = part.strip().split(";")[0]
    if kv.startswith("__Secure-neon-auth.session_token="):
        ck = kv.strip()
if not ck:
    ck = "__Secure-neon-auth.session_token=" + json.loads(raw).get("token", "")
st, raw2, _ = req(NA, "GET", "/neondb/auth/token", hdr={"Cookie": ck})
jwt = json.loads(raw2)["token"]
h_part, p_part, s_part = jwt.split(".")
# 2. publicKey from DB
import psycopg
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
conn = http.client.HTTPSConnection("console-stage.neon.build", timeout=30, context=ctx)
conn.request("GET", "/api/v2/projects/orange-sun-90493739/connection_uri"
             "?database_name=neondb&role_name=neondb_owner"
             "&branch_id=br-wandering-field-w2ob6mpn",
             headers={"X-Bug-Bounty": "xxbo",
                      "Authorization": "Bearer " + json.load(open(r"F:\scan\neon_report\_apikey.json"))["key"]})
r = conn.getresponse()
uri = json.loads(r.read().decode())["uri"]
conn.close()
p = urlsplit(uri)
q = [(k, v) for k, v in parse_qsl(p.query) if k != "channel_binding"]
uri2 = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
with psycopg.connect(uri2, connect_timeout=15) as dbc:
    dbc.autocommit = True
    with dbc.cursor() as cur:
        cur.execute('SELECT "publicKey" FROM neon_auth.jwks')
        pubj = json.loads(cur.fetchone()[0])
x = b64d(pubj["x"])
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
pub = Ed25519PublicKey.from_public_bytes(x)
try:
    pub.verify(b64d(s_part), (h_part + "." + p_part).encode())
    print("VERIFY: real JWT signature VALID under stored publicKey -> this keypair signs tokens")
except InvalidSignature:
    print("VERIFY: signature INVALID -> stored keypair NOT the signer")
except Exception as e:
    print("verify err:", str(e)[:150])
# 3. check blob ASCII profile (hex-of-hex?)
with psycopg.connect(uri2, connect_timeout=15) as dbc:
    dbc.autocommit = True
    with dbc.cursor() as cur:
        cur.execute('SELECT "privateKey" FROM neon_auth.jwks')
        priv = json.loads(cur.fetchone()[0])
b = bytes.fromhex(priv)
print("blob printable ratio:", sum(1 for x in b if 32 <= x < 127) / len(b))
print("blob head ascii:", b[:60])
