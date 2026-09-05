# -*- coding: utf-8 -*-
"""analyze 169-byte private key blob structure + try loaders"""
import json, ssl, time, http.client

ctx = ssl.create_default_context()
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
        cur.execute('SELECT "privateKey", "publicKey" FROM neon_auth.jwks')
        priv, pub = cur.fetchone()
s = json.loads(priv)
b = bytes.fromhex(s)
print("total bytes:", len(b))
print("first 32 hex:", s[:64])
print("last 32 hex:", s[-64:])
print("byte 0-15:", b[:16].hex())
# try candidate seeds against public key x
pubx = json.loads(pub)["x"]
import base64
def b64u(raw):
    return base64.b64encode(raw).decode().replace("+", "-").replace("/", "_").rstrip("=")
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
cands = {
    "first32": b[:32],
    "last32": b[-32:],
    "bytes32-64": b[32:64],
}
for name, seed in cands.items():
    try:
        sk = Ed25519PrivateKey.from_private_bytes(seed)
        pk = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        print("%-12s pub=%s match=%s" % (name, b64u(pk), b64u(pk) == pubx))
    except Exception as e:
        print(name, "err", str(e)[:60])
# try DER loaders on whole blob / substrings
for name, blob in [("whole", b), ("first48", b[:48])]:
    try:
        k = serialization.load_der_private_key(blob, password=None)
        print("%-8s DER load OK type=%s" % (name, type(k).__name__))
    except Exception as e:
        print("%-8s DER load err %s" % (name, str(e)[:70]))
# maybe hex string itself is a JWK JSON-encoded differently: check if it contains non-hex later
print("all hex:", all(c in "0123456789abcdef" for c in s))
