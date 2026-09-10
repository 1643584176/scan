# -*- coding: utf-8 -*-
"""ET53: find real call-sites & params for search endpoints in z page bundles"""
import os, re

JS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
FILES = [
    "z_pages-Search-19402afa43cd46f9047b.js",
    "z_zomato-5b4c68bb1f2c1592a059.js",
    "z_layoutEntries-searchDesktopIndex-dc423479412fc1cc3c30.js",
    "z_layoutEntries-uniSearchDesContainer-a105a76fa4d68a81add7.js",
    "z_RestaurantCardV2-8514e8764c02f001f2ae.js",
]
KWS = ["autoSuggest", "searchapi", "applyFilter", "search/home", "query=", "?q=", "searchText", "search_text",
       "entity_id", "entity_type", "res_id", "city_id", "fetch(", "ajax", "XMLHttpRequest"]

seen = set()
for f in FILES:
    p = os.path.join(JS_DIR, f)
    if not os.path.exists(p):
        continue
    data = open(p, "r", encoding="utf-8", errors="replace").read()
    print("#### %s (len=%d) ####" % (f[:45], len(data)), flush=True)
    for kw in KWS:
        idx, cnt = 0, 0
        while cnt < 4:
            idx = data.find(kw, idx)
            if idx < 0:
                break
            seg = re.sub(r"\s+", " ", data[max(0, idx - 260):idx + 340])
            key = (f[:20], seg[:120])
            if key not in seen:
                seen.add(key)
                print("[%s] %s" % (kw, seg[:560]), flush=True)
            idx += len(kw)
            cnt += 1
print("done", flush=True)
