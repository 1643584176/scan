# -*- coding: utf-8 -*-
# _peek_an2.py - dump all methods of analytics v2 client class in net_lib.js
import re

src = open(r"D:/scan/netlify_report/_js/net_lib.js", encoding="utf-8", errors="replace").read()

# find class whose constructor uses analyticsClientApiBase (apiVersion v2)
i = src.find('analyticsClientApiBase')
# expand to class end: find next '},' boundary after methods; simpler: dump 60KB after the class start
start = src.rfind("return e=[{key:", 0, i)
seg = src[start:start + 80000]
# print all key: method names with their request paths
for m in re.finditer(r'key:"([A-Za-z0-9_]+)"', seg):
    pass
# extract method name -> path pairs
pairs = []
for m in re.finditer(r'key:"([A-Za-z0-9_]+)",value:function\(([^)]*)\)\{(.*?)(?=key:"|\},function)', seg, re.S):
    name, args, body = m.group(1), m.group(2), m.group(3)
    pm = re.search(r'this\.request\("([^"]+)"', body) or re.search(r'this\.request\(([^,)]+)\)', body)
    if pm:
        pairs.append((name, pm.group(1)))
for n, p in pairs:
    print("%-40s %s" % (n, p[:200]))
