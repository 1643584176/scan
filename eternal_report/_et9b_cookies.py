# -*- coding: utf-8 -*-
"""extract cookie names + token handling from district JS"""
import re, os

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
data = open(os.path.join(d, "ds_2t5m6l255zvhn.js"), encoding="utf-8", errors="replace").read()
cookies = set(re.findall(r'(?:getCookie|setCookie|removeCookie|deleteCookie)\(\s*["\']([a-zA-Z0-9_\-]+)["\']', data))
print("cookies:", sorted(cookies))
toks = set(re.findall(r'["\']([a-zA-Z0-9_\-]*(?:access|refresh|auth|ed|session)[a-zA-Z0-9_\-]*token[a-zA-Z0-9_\-]*)["\']', data, re.I))
print("token-like:", sorted(toks))
# find where refresh cookie is read/written with context
for m in re.finditer(r'.{80}(?:access_token|refresh_token|accessToken|refreshToken|ed_token).{120}', data):
    s = m.group(0)
    if "cookie" in s.lower() or "document" in s.lower() or "localStorage" in s.lower():
        print("CTX:", s[:260].replace("\n", " "), "\n---")
