# -*- coding: utf-8 -*-
"""ET51: extract search-API calls & real param names from z_*.js (zomato search page bundles) + all JS"""
import os, re, glob

JS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
files = sorted(glob.glob(os.path.join(JS_DIR, "z_*.js"))) + sorted(glob.glob(os.path.join(JS_DIR, "*.js")))

pats = [
    ("SEARCHAPI", re.compile(r'.{60}searchapi.{100}', re.I)),
    ("SEARCHURL", re.compile(r'["\'](?:https?:)?//[^"\']{0,120}(?:/search|searchapi|suggest|autocomplete)[^"\']{0,140}["\']', re.I)),
    ("QPARAM", re.compile(r'[?&](?:q|query|search|term|keyword|entity_id|entity_type|res_id|city_id|action|screen_size|user_lat|user_lon)=[^"\',&\s]{0,30}', re.I)),
]

seen = set()
for fn in files:
    try:
        data = open(fn, "r", encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    name = os.path.basename(fn)
    for typ, rx in pats:
        for m in rx.finditer(data):
            s = re.sub(r"\s+", " ", m.group(0))[:220]
            key = (typ, s)
            if key in seen:
                continue
            seen.add(key)
            print("[%s|%s] %s" % (typ, name[:28], s), flush=True)
print("total %d unique" % len(seen), flush=True)
