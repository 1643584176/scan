# -*- coding: utf-8 -*-
# _peek_libpaths.py - extract all request() path patterns from net_lib.js with method names
import re

src = open(r"D:/scan/netlify_report/_js/net_lib.js", encoding="utf-8", errors="replace").read()

# patterns like: key:"someMethod",value:function(...){...this.request("/path"...
# simpler: find this.request("/...") occurrences and show context with nearby key:"name"
pat = re.compile(r'this\.request\("(/[^"]{2,160})')
for m in pat.finditer(src):
    # find enclosing method key name: search backward for key:"..."
    back = src[max(0, m.start() - 1200):m.start()]
    km = list(re.finditer(r'key:"([A-Za-z0-9_]+)"', back))
    kname = km[-1].group(1) if km else "?"
    print("%-38s %s" % (kname, m.group(1)))
