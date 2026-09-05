# -*- coding: utf-8 -*-
"""Pull console-stage.neon.build HTML -> find JS bundle -> download -> grep for
schema_only / new-feature endpoints not present in the OpenAPI spec."""
import re
import ssl
import urllib.request

ctx = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    d = urllib.request.urlopen(req, context=ctx, timeout=60).read()
    return d if binary else d.decode("utf-8", "replace")


html = get("https://console-stage.neon.build/")
js_urls = re.findall(r'<script[^>]+src="([^"]+\.js[^"]*)"', html)
print("scripts:", js_urls[:10])
cands = [u for u in js_urls if "main" in u or "index" in u or "app" in u]
if not cands:
    cands = js_urls
for u in cands[:4]:
    url = u if u.startswith("http") else "https://console-stage.neon.build" + u
    try:
        data = get(url)
        print("fetched", url, len(data))
        out = r"F:\scan\neon_report\_console_js.bin" if url.endswith(".js") else r"F:\scan\neon_report\_console_main.js"
        open(out, "w", encoding="utf-8", errors="replace").write(data)
        print("saved ->", out)
        for kw in ["schema_only", "schema-only", "schemaOnly", "branch_mode", "branchMode"]:
            idxs = [m.start() for m in re.finditer(kw, data)]
            print("kw", kw, "hits:", len(idxs))
            for i in idxs[:5]:
                print("   ...", data[max(0, i - 200):i + 200].replace("\n", " ")[:400])
        break
    except Exception as e:
        print("ERR", url, str(e)[:150])
