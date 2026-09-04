# -*- coding: utf-8 -*-
# _peek_an4.py - raw context dump around analytics method names
import re

src = open(r"D:/scan/netlify_report/_js/net_lib.js", encoding="utf-8", errors="replace").read()
i = src.find('analyticsClientApiBase')
start = src.rfind("return e=[{key:", 0, i)
seg = src[start:start + 120000]

for name in ("pageviews", "uniqueVisitors", "accountBuildsUsageTimeseries"):
    m = re.search(r'key:"' + name + '"', seg)
    if not m:
        print("### %s NOT FOUND" % name)
        continue
    s = max(0, m.start() - 200)
    e = min(len(seg), m.start() + 1600)
    print("### %s" % name)
    print(seg[s:e])
    print()
