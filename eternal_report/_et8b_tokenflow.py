# -*- coding: utf-8 -*-
"""extract auth/token flow from district JS chunks"""
import os, re, glob

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
focused = ["ds_27ozuboy-mg1z.js", "tn_2aoz8lvlm7mvq.js", "ds_2t5m6l255zvhn.js", "tn_41p6l24qifb-y.js", "ds_3f6vvan9pcth8.js", "tn_45671znofo_bp.js"]
for fn in focused:
    data = open(os.path.join(d, fn), encoding="utf-8", errors="replace").read()
    auths = set(re.findall(r'["\'](/auth/[a-zA-Z0-9_/.\-]*)["\']', data)) | set(re.findall(r'["\'](/gw/auth[a-zA-Z0-9_/.\-]*)["\']', data))
    if auths:
        print(fn, "->", sorted(auths))
print("\n-- access token obtain context --")
data = open(os.path.join(d, "ds_2t5m6l255zvhn.js"), encoding="utf-8", errors="replace").read()
for m in re.finditer(r'.{150}/auth/refresh_token.{200}', data):
    print(m.group(0)[:400], "\n---")
