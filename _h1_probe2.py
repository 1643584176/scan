# -*- coding: utf-8 -*-
"""probe policy_scopes.json accept variants"""
import http.client, ssl

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"


def fetch(path, accept, referer=None):
    conn = http.client.HTTPSConnection("hackerone.com", timeout=30, context=ctx)
    h = {"User-Agent": UA, "Accept": accept}
    if referer:
        h["Referer"] = referer
    conn.request("GET", path, headers=h)
    r = conn.getresponse()
    raw = r.read().decode("utf-8", "replace")
    ct = r.getheader("Content-Type")
    conn.close()
    return r.status, ct, raw[:800]


def main():
    for acc in ("text/html", "application/json", "*/*", "text/plain",
                "application/vnd.hackerone+json; version=1.0"):
        st, ct, b = fetch("/eternal/policy_scopes.json", acc)
        print("accept=%s -> [%d] ct=%s %s" % (acc, st, ct, b.replace("\n", " ")[:400]), flush=True)
    # with referer
    st, ct, b = fetch("/eternal/policy_scopes.json", "application/json", "https://hackerone.com/eternal")
    print("referer -> [%d] ct=%s %s" % (st, ct, b.replace("\n", " ")[:400]), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
