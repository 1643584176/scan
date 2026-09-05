# -*- coding: utf-8 -*-
"""ET2: grab robots + tiny bodies from live assets (read-only)"""
import http.client, ssl, socket, threading, re
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

JOBS = [
    ("www.runnr.in", "/", "runnr_root"),
    ("www.runnr.in", "/robots.txt", "runnr_robots"),
    ("bugbounty.runnr.in", "/robots.txt", "bugbounty_robots"),
    ("mcp-server.zomato.com", "/mcp", "mcp_get"),
    ("mcp-server.zomato.com", "/openapi.json", "mcp_openapi"),
    ("winecellar.zomato.com", "/", "winecellar_root"),
    ("www.ticketnew.com", "/", "ticketnew_root"),
    ("www.tktnew.com", "/", "tktnew_root"),
    ("www.tktnew.com", "/robots.txt", "tktnew_robots"),
    ("www.district.in", "/robots.txt", "district_robots"),
    ("www.zomato.com", "/robots.txt", "zomato_robots"),
    ("www.hyperpure.com", "/robots.txt", "hyperpure_robots"),
]


def fetch(h, path, name):
    out = ["==== %s  (GET %s%s) ====" % (name, h, path)]
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=10, context=ctx)
        conn.request("GET", path, headers={
            "User-Agent": UA, "Accept": "text/html,application/json,text/plain,*/*;q=0.8"})
        r = conn.getresponse()
        raw = r.read(30000)
        body = raw.decode("utf-8", "replace")
        conn.close()
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        out.append("status=%d ct=%s server=%s loc=%s" % (
            r.status, hdrs.get("content-type", "-")[:40], hdrs.get("server", "-"),
            hdrs.get("location", "")))
        # strip html tags for readability
        if r.status not in (301, 302, 303, 307, 308) and "text/html" in hdrs.get("content-type", ""):
            txt = re.sub(r"<script.*?</script>", "", body, flags=re.S)
            txt = re.sub(r"<style.*?</style>", "", txt, flags=re.S)
            txt = re.sub(r"<[^>]+>", " ", txt)
            txt = re.sub(r"\s+", " ", txt).strip()
            out.append("TEXT: %s" % txt[:600])
        else:
            out.append("BODY: %s" % body[:1500])
    except Exception as e:
        out.append("EXC %s" % repr(e)[:100])
    return "\n".join(out) + "\n"


def main():
    with ThreadPoolExecutor(max_workers=5) as ex:
        for res in ex.map(lambda j: fetch(*j), JOBS):
            print(res, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
