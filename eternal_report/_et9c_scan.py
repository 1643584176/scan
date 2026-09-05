# -*- coding: utf-8 -*-
"""scan all chunks for cookie names + Authorization/token header setup"""
import re, os, glob

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
files = glob.glob(os.path.join(d, "*.js"))
cookies = {}
authhdr = {}
for fn in files:
    name = os.path.basename(fn)
    data = open(fn, encoding="utf-8", errors="replace").read()
    cs = set(re.findall(r'(?:getCookie|setCookie|readCookie|eraseCookie|deleteCookie|removeCookie)\(\s*["\']([a-zA-Z0-9_\-]+)["\']', data))
    for c in cs:
        cookies.setdefault(c, []).append(name)
    if "Authorization" in data or "authorization" in data:
        # find assignment lines
        for m in re.finditer(r'.{0,60}["\']authorization["\']\s*[:=]\s*["\']?([^,;}\n]{0,120})', data, re.I):
            authhdr.setdefault(m.group(1)[:80], []).append(name)
print("== cookie names ==")
for c in sorted(cookies):
    print("%-30s %s" % (c, ",".join(sorted(set(cookies[c]))[:3])))
print("\n== authorization assignments ==")
for a in sorted(authhdr):
    print("%-90s %s" % (a, ",".join(sorted(set(authhdr[a]))[:3])))
