# -*- coding: utf-8 -*-
"""fetch H1 eternal policy pages - look for embedded JSON data"""
import http.client, ssl, re, json

ctx = ssl.create_default_context()


def fetch(path):
    conn = http.client.HTTPSConnection("hackerone.com", timeout=30, context=ctx)
    conn.request("GET", path, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml"})
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def main():
    for p in ("/eternal/policy_scopes", "/eternal", "/eternal/embedded?type=team"):
        st, raw = fetch(p)
        print("== %s [%d] len=%d" % (p, st, len(raw)), flush=True)
        # look for embedded JSON state
        for pat in ("window.h1", "__NUXT__", "policy_scopes", "in_scope", "bounty", "assets"):
            idxs = [m.start() for m in re.finditer(re.escape(pat), raw)][:3]
            if idxs:
                for i in idxs:
                    print("  %s @%d: %s" % (pat, i, raw[max(0, i - 80):i + 200].replace("\n", " ")[:280]), flush=True)
        # any JSON-LD?
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
        if m:
            print("  json-ld:", m.group(1)[:500], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
