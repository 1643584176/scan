# -*- coding: utf-8 -*-
"""ET57: extract __PRELOADED_STATE__ + download missing chunks + local grep for search call-sites"""
import re, os, ssl, http.client, time

D = os.path.dirname(os.path.abspath(__file__))
JS = os.path.join(D, "_js")
ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36"

# ---- 1) __PRELOADED_STATE__ ----
html = open(os.path.join(D, "_zomato_search.html"), "r", encoding="utf-8", errors="replace").read()
i = html.find("__PRELOADED_STATE__")
print("== PRELOADED_STATE idx=%d ==" % i, flush=True)
seg = html[i:i + 4000]
print(re.sub(r"\s+", " ", seg)[:3800], flush=True)

# ---- 2) download missing chunks ----
CHUNKS = ["4526-1a53c495f1df6335f982.js", "3550-f59fe92ee3071a918bf6.js", "3813-a7f7196b74aa09a649d8.js",
          "9693-a8cec1e245e3e83b671a.js", "5606-47f7d653f14da644831b.js", "9358-6992402b8c86ecefd39a.js",
          "6347-942bf2612b8cba7457d3.js", "2051-80568c8a79e7ddb1e06d.js", "6434-253400b78d8de2729877.js",
          "6810-0bfd08cea4571af43e32.js", "5879-97af0073e8c874efd878.js", "3598-314d7bd54d175cebd8f0.js",
          "4304-da3ac262712e693dd0b3.js", "9955-9a351ef642bb1f78b3de.js", "8640-4201d6caaeb9ae273429.js",
          "3439-8a802eed5b501c3ab275.js", "289-18f9686cf8f7fdee6f28.js", "3419-760b3498c94bc55b0397.js"]
print("\n== downloading %d chunks ==" % len(CHUNKS), flush=True)
for c in CHUNKS:
    fp = os.path.join(JS, "zc_" + c)
    if os.path.exists(fp):
        print("  [have] %s" % c, flush=True)
        continue
    try:
        conn = http.client.HTTPSConnection("zwstatic.zomato.com", 443, timeout=20, context=ctx)
        conn.request("GET", "/" + c, headers={"User-Agent": UA})
        r = conn.getresponse()
        raw = r.read()
        conn.close()
        open(fp, "wb").write(raw)
        print("  [%d %d bytes] %s" % (r.status, len(raw), c), flush=True)
    except Exception as e:
        print("  [EXC %s] %s" % (repr(e)[:60], c), flush=True)
    time.sleep(0.5)

# ---- 3) local grep in downloaded chunks ----
print("\n== grep search call-sites ==", flush=True)
KW = ["searchapi", "autoSuggest", "search/home", "applyFilter"]
for f in sorted(os.listdir(JS)):
    if not f.startswith("zc_"):
        continue
    data = open(os.path.join(JS, f), "r", encoding="utf-8", errors="replace").read()
    for kw in KW:
        idx = data.find(kw)
        if idx >= 0:
            seg = re.sub(r"\s+", " ", data[max(0, idx - 300):idx + 400])
            print("[%s|%s] %s" % (f[:30], kw, seg[:640]), flush=True)
print("done", flush=True)
