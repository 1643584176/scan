# -*- coding: utf-8 -*-
"""ET52: dump call-sites of real search endpoints in z_main js to recover param construction"""
import os, re

JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js", "z_main-8efa4cf644fa76389041.js")
data = open(JS, "r", encoding="utf-8", errors="replace").read()
print("file len:", len(data))

kws = ["searchapi.php", "handlers/Search/index.php", "webroutes/location/search", "locationGeoData", "webapi/"]
out = []
for kw in kws:
    idx, cnt = 0, 0
    while cnt < 8:
        idx = data.find(kw, idx)
        if idx < 0:
            break
        seg = re.sub(r"\s+", " ", data[max(0, idx - 380):idx + 500])
        out.append("=== %s @%d ===\n%s" % (kw, idx, seg))
        idx += len(kw)
        cnt += 1

txt = "\n\n".join(out)
open("_et52_out.txt", "w", encoding="utf-8").write(txt)
print(txt[:12000], flush=True)
print("saved _et52_out.txt", flush=True)
