# -*- coding: utf-8 -*-
# _peek_an3.py - dump full body of analytics v2 methods: pageviews + account timeseries
import re

src = open(r"D:/scan/netlify_report/_js/net_lib.js", encoding="utf-8", errors="replace").read()
i = src.find('analyticsClientApiBase')
start = src.rfind("return e=[{key:", 0, i)
seg = src[start:start + 120000]

for name in ("pageviews", "accountBuildsUsageTimeseries", "uniqueVisitors", "historicalFunctionLogs"):
    m = re.search(r'key:"%s",value:function\((.*?)\}\},function' % name, seg, re.S)
    if m:
        print("### %s" % name)
        print(m.group(0)[:2500])
        print()
