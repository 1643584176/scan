# -*- coding: utf-8 -*-
"""ET34: download access.zomans.com angular bundles + grep auth/endpoints"""
import http.client, ssl, re, os

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
BASE = "access.zomans.com"

def fetch(path):
    conn = http.client.HTTPSConnection(BASE, 443, timeout=20, context=ctx)
    conn.request("GET", path, headers={"User-Agent": UA, "Accept": "*/*"})
    r = conn.getresponse()
    raw = r.read()
    conn.close()
    print("%-40s [%d] len=%d ct=%s" % (path, r.status, len(raw), r.headers.get("Content-Type", "-")), flush=True)
    return raw

os.makedirs("_zm_js", exist_ok=True)
for j in ["runtime.8f8351b65238f278.js", "polyfills.374c7c60e79cd750.js",
          "scripts.3530fe8fed3a0d79.js", "main.6d67864266419798.js"]:
    try:
        raw = fetch("/" + j)
        open(os.path.join("_zm_js", j), "wb").write(raw)
    except Exception as e:
        print(j, "EXC", repr(e)[:80], flush=True)

print("\n== grep main.js ==")
for j in ["main.6d67864266419798.js", "scripts.3530fe8fed3a0d79.js"]:
    p = os.path.join("_zm_js", j)
    if not os.path.exists(p):
        continue
    s = open(p, "r", encoding="utf-8", errors="replace").read()
    print("--- %s len=%d ---" % (j, len(s)))
    print("== urls ==")
    for m in sorted(set(re.findall(r'["\'](/[a-zA-Z0-9_\-./]{2,120})["\']', s))):
        if re.search(r'(auth|login|sso|token|session|bubble|route|verify|otp|password|user|register|signup|forgot|reset|api|graphql|oauth|google|github|redirect|code)', m, re.I):
            print(" ", m[:150])
    print("== http calls ==")
    for m in sorted(set(re.findall(r'["\'](https?://[^"\']+)["\']', s)))[:60]:
        print(" ", m[:150])
    print("== login method kws ==")
    for kw in ["email", "password", "google", "phone", "otp", "sso", "bubble", "redirect_url", "client_id", "grant_type"]:
        idxs = [mm.start() for mm in re.finditer(kw, s, re.I)][:4]
        for i in idxs:
            seg = s[max(0, i - 80):i + 120]
            seg = re.sub(r"\s+", " ", seg)
            print(" KW %s: %s" % (kw, seg[:200]))
    print()
print("done", flush=True)
