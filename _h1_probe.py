# -*- coding: utf-8 -*-
"""probe H1 public API shapes for team eternal"""
import http.client, ssl, re, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"


def fetch(host, path, extra=None):
    conn = http.client.HTTPSConnection(host, timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": "application/json"}
    if extra:
        h.update(extra)
    conn.request("GET", path, headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    conn.close()
    return r.status, raw


def main():
    probes = [
        ("hackerone.com", "/api/v1/teams/eternal"),
        ("hackerone.com", "/eternal.json"),
        ("hackerone.com", "/graphql"),
        ("hackerone.com", "/api/v1/teams/eternal/policy"),
        ("hackerone.com", "/eternal/policy_scopes.json"),
    ]
    for host, p in probes:
        st, b = fetch(host, p)
        print("== %s%s [%d] %s" % (host, p, st, b[:400].replace("\n", " ")), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
