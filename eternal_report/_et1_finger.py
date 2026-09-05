# -*- coding: utf-8 -*-
"""ET1: Eternal in-scope asset reachability + fingerprint (read-only, 1 req per host, concurrent)"""
import http.client, ssl, socket, re, threading
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# in-scope hosts to fingerprint
HOSTS = [
    # Tier 1 / new finds
    "www.zomato.com", "winecellar.zomato.com", "mcp-server.zomato.com",
    "www.runnr.in", "bugbounty.runnr.in", "www.zomans.com",
    # Tier 2
    "www.blinkit.com", "api.grofers.com", "api2.grofers.com", "www.grofers.com",
    "www.grofer.io", "www.hyperpure.com", "www.district.in", "bistro-api.blinkit.com",
    # Tier 3
    "www.insider.in", "www.edition.in", "www.ticketnew.com", "www.tktnew.com",
    "www.eternal.com",
]


def dns(h):
    """resolve with hard timeout via thread"""
    res = []

    def _r():
        try:
            infos = socket.getaddrinfo(h, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
            a4 = next((i[4][0] for i in infos if i[0] == socket.AF_INET), "?")
            a6 = next((i[4][0] for i in infos if i[0] == socket.AF_INET6), "-")
            res.append((a4, a6[:40]))
        except Exception as e:
            res.append(("DNS_ERR", repr(e)[:60]))

    t = threading.Thread(target=_r, daemon=True)
    t.start()
    t.join(8)
    if not res:
        return ("DNS_TO", "-")
    return res[0]


def probe(h):
    out = []
    a4, a6 = dns(h)
    out.append("%-24s A=%-16s A6=%s" % (h, a4, a6))
    if a4 in ("DNS_ERR", "DNS_TO", "?"):
        return out
    for path in ("/", "/robots.txt"):
        try:
            conn = http.client.HTTPSConnection(h, 443, timeout=10, context=ctx)
            conn.request("GET", path, headers={
                "User-Agent": UA, "Accept": "text/html,application/json,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"})
            r = conn.getresponse()
            raw = r.read(12000)
            body = raw.decode("utf-8", "replace")
            conn.close()
            hdrs = dict((k.lower(), v) for k, v in r.getheaders())
            title = ""
            m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
            if m:
                title = m.group(1).strip()[:80]
            out.append("  %-11s [%d] srv=%s ct=%s len=%d %s" % (
                path, r.status, hdrs.get("server", "-")[:25],
                (hdrs.get("content-type") or "")[:30], len(raw),
                ("title=%s" % title if title else ("loc=%s" % hdrs.get("location", "")[:80] if r.status in (301, 302, 303, 307, 308) else ""))))
        except Exception as e:
            out.append("  %-11s EXC %s" % (path, repr(e)[:90]))
    return out


def main():
    print("== ET1 fingerprint (concurrent) ==", flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        for lines in ex.map(probe, HOSTS):
            for l in lines:
                print(l, flush=True)
            print("", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
