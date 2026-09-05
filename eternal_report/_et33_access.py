# -*- coding: utf-8 -*-
"""ET33: access.zomans.com login page analysis"""
import http.client, ssl, re, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

conn = http.client.HTTPSConnection("access.zomans.com", 443, timeout=15, context=ctx)
conn.request("GET", "/", headers={"User-Agent": UA, "Accept": "text/html"})
r = conn.getresponse()
raw = r.read(200000)
conn.close()
body = raw.decode("utf-8", "replace")
print("len=%d ct=%s" % (len(raw), r.headers.get("Content-Type", "-")))
open("_access_login.html", "w", encoding="utf-8").write(body)

# login form fields / api endpoints / js
print("\n== forms ==")
for m in re.finditer(r'<form[^>]*>.*?</form>', body, re.S):
    print(m.group(0)[:800], "\n---")
print("\n== input fields ==")
for m in re.finditer(r'<input[^>]*>', body):
    s = m.group(0)
    if "type" in s and "hidden" not in s:
        print(s[:200])
print("\n== js srcs ==")
for m in re.finditer(r'<script[^>]+src="([^"]+)"', body):
    print(m.group(1))
print("\n== auth api hints ==")
for m in sorted(set(re.findall(r'["\'](/[a-zA-Z0-9_\-./]*(?:auth|login|sso|token|session|bubble|route|verify|otp|password)[a-zA-Z0-9_\-./]*)["\']', body, re.I))):
    print(m)
print("\n== email/phone/oauth text ==")
for kw in ["email", "Email", "phone", "Phone", "Google", "SSO", "sso", "continue", "Sign in", "sign in", "Sign up"]:
    i = body.find(kw)
    if i >= 0:
        print("KW %s: %s" % (kw, re.sub(r"<[^>]+>", " ", body[max(0, i - 100):i + 150]).replace("\n", " ")[:200]))
print("done", flush=True)
