# -*- coding: utf-8 -*-
"""ET16: context around zomato search endpoints in main bundle"""
import os, re, json

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
data = open(os.path.join(d, "z_main-8efa4cf644fa76389041.js"), encoding="utf-8", errors="replace").read()

print("== context around key endpoints ==")
for target in ["/webapi/searchapi.php", "/webroutes/search/applyFilter", "/webroutes/search/autoSuggest",
               "/webroutes/search/home", "/api/fetch"]:
    print("\n--- %s ---" % target)
    cnt = 0
    for m in re.finditer(re.escape(target), data):
        s = max(0, m.start() - 200)
        ctx = data[s:m.end() + 300]
        print("CTX:", ctx.replace("\n", " ")[:480], "\n")
        cnt += 1
        if cnt >= 2:
            break

print("\n== searchapi.php param construction ==")
for m in re.finditer(r'.{80}searchapi\.php.{250}', data):
    print(m.group(0)[:400], "\n---")
print("done", flush=True)
