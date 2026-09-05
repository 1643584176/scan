# -*- coding: utf-8 -*-
"""ET32: follow zomans redirects + root body"""
import http.client, ssl, time, re

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def follow(h, path="/", depth=0, seen=None):
    seen = seen or []
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=10, context=ctx)
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"})
        r = conn.getresponse()
        raw = r.read(200000)
        conn.close()
        h2 = dict((k.lower(), v) for k, v in r.getheaders())
        loc = h2.get("location", "")
        print("%s%s%s [%d] loc=%s ct=%s len=%d" % ("  " * depth, h, path, r.status, loc[:120], h2.get("content-type", "-")[:24], len(raw)), flush=True)
        if r.status in (301, 302, 303, 307, 308) and loc and depth < 4:
            # absolute vs relative
            if loc.startswith("http"):
                from urllib.parse import urlparse
                u = urlparse(loc)
                if u.hostname and u.hostname != h:
                    return follow(u.hostname, u.path or "/", depth + 1)
                return follow(h, u.path + (("?" + u.query) if u.query else ""), depth + 1)
            return follow(h, loc, depth + 1)
        body = raw.decode("utf-8", "replace")
        m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
        t = m.group(1).strip()[:80] if m else ""
        if t:
            print("  " * (depth + 1) + "title:", t, flush=True)
        else:
            print("  " * (depth + 1) + "body:", body[:200].replace("\n", " "), flush=True)
        return raw
    except Exception as e:
        print("%sEXC %s" % ("  " * depth, repr(e)[:90]), flush=True)
        return b""

for h in ["admin.zomans.com", "api.zomans.com"]:
    print("== %s ==" % h)
    follow(h)
    time.sleep(1)
print("done", flush=True)
