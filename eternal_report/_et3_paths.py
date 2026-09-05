# -*- coding: utf-8 -*-
"""ET3: bugbounty.runnr.in path discovery + ticketnew.com bare domain (low-volume, read-only)"""
import http.client, ssl, re
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# Rails-ish / common paths on the bugbounty replica + ticketnew main
PATHS_BB = [
    "/login", "/sign_in", "/users/sign_in", "/signup", "/sign_up", "/users/sign_up",
    "/admin", "/admin/login", "/dashboard", "/home", "/index", "/app", "/orders",
    "/order", "/api", "/api/v1", "/api/v2", "/v1", "/v2", "/graphql", "/health",
    "/healthz", "/status", "/version", "/ping", "/heartbeat", "/favicon.ico",
    "/swagger", "/swagger-ui", "/docs", "/redoc", "/assets", "/uploads", "/images",
    "/users", "/me", "/account", "/profile", "/settings", "/logout", "/session",
    "/cities", "/restaurants", "/search", "/explore", "/track", "/delivery",
    "/rider", "/driver", "/fleet", "/partners", "/merchant", "/webhook", "/cron",
]
PATHS_TN = ["/", "/login", "/signin", "/register", "/movies", "/events", "/api", "/health", "/robots.txt", "/admin"]

def fetch(h, path):
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=8, context=ctx)
        conn.request("GET", path, headers={
            "User-Agent": UA, "Accept": "text/html,application/json,*/*;q=0.7",
            "Accept-Language": "en-US,en;q=0.9"})
        r = conn.getresponse()
        raw = r.read(4000)
        body = raw.decode("utf-8", "replace")
        conn.close()
        hdrs = dict((k.lower(), v) for k, v in r.getheaders())
        ct = hdrs.get("content-type", "")[:35]
        loc = hdrs.get("location", "")[:90]
        sig = ""
        if r.status == 200:
            m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
            sig = ("title=" + m.group(1).strip()[:60]) if m else body[:80].replace("\n", " ")
        return (h, path, r.status, ct, loc, sig)
    except Exception as e:
        return (h, path, -1, "EXC", "", repr(e)[:60])


def run(h, paths, tag):
    print("==== %s on %s (%d paths) ====" % (tag, h, len(paths)), flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        for host, p, st, ct, loc, sig in ex.map(lambda x: fetch(*x), [(h, p) for p in paths]):
            if st in (200, 301, 302, 303, 307, 308, 401, 403, 405, 500, 501):
                print("%-5s %-22s [%d] %s %s %s" % (tag, p, st, ct, ("-> " + loc if loc else ""), sig[:80]), flush=True)
    print("", flush=True)


def main():
    run("bugbounty.runnr.in", PATHS_BB, "BB")
    run("ticketnew.com", PATHS_TN, "TN")
    run("www.tktnew.com", ["/orders", "/order", "/login", "/signin", "/track", "/status", "/api", "/v1"], "TK")
    print("done", flush=True)


if __name__ == "__main__":
    main()
