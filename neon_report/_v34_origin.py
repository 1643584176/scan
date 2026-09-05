# -*- coding: utf-8 -*-
"""V34: verify _js origin (stage vs prod markers) + neonauth host root/static + stage console asset paths"""
import re, ssl, http.client, json, os

ctx = ssl.create_default_context()
NA = "ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build"


def get(host, path, hdr=None):
    conn = http.client.HTTPSConnection(host, timeout=25, context=ctx)
    h = {"User-Agent": "Mozilla/5.0"}
    if hdr:
        h.update(hdr)
    conn.request("GET", path, headers=h)
    r = conn.getresponse()
    d = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, r.getheader("Content-Type", ""), d


def main():
    # 1. markers in local app.js
    for marker in ("console-stage", "console.neon.tech", "staging-realm", "I-LOVE-PREVIEWS",
                   "neon.tech", "databricks", "accounts.cloud.databricks"):
        n = 0
        for f in (r"F:\scan\neon_report\_js\app.js",):
            s = open(f, encoding="utf-8", errors="replace").read()
            n += len(re.findall(re.escape(marker), s))
        print("marker %-30s count=%d" % (marker, n))
    # 2. stage console asset manifest (chunk list = endpoint surface hint)
    st, ct, d = get("console-stage.neon.build", "/", hdr={"X-Bug-Bounty": "xxbo"})
    print("\nstage / -> %d %s len=%d" % (st, ct, len(d)))
    m = re.findall(r'assets/[A-Za-z0-9_\-\.]+\.js', d)[:10]
    print("stage script assets sample:", m[:5])
    # 3. neonauth host static/root surface
    for p in ("/", "/neondb/auth/sign-in", "/neondb/auth/sign-in/email",
              "/neondb/auth/verify-email", "/neondb/auth/forget-password",
              "/neondb/auth/error", "/neondb/auth/.well-known/jwks.json"):
        try:
            st2, ct2, d2 = get(NA, p)
            print("NA GET %-38s -> %d %s %s" % (p, st2, ct2[:30], d2[:60].replace("\n", " ")))
        except Exception as ex:
            print("NA GET %-38s -> ERR %s" % (p, ex))


if __name__ == "__main__":
    main()
