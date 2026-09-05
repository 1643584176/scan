# -*- coding: utf-8 -*-
"""ET8: probe api.edition.in gateway shape (read-only GETs)"""
import http.client, ssl, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

TESTS = [
    ("/gw/consumer/movies/v3/cities", {}),
    ("/consumer/movies/v3/cities", {}),
    ("/gw/consumer/movies/v3/cities", {"Origin": "https://www.district.in", "Referer": "https://www.district.in/"}), 
    ("/consumer/web/pre_home", {"Origin": "https://www.district.in", "Referer": "https://www.district.in/"}),
]


def req(h, path, extra=None):
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=10, context=ctx)
        hdrs = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
        if extra:
            hdrs.update(extra)
        conn.request("GET", path, headers=hdrs)
        r = conn.getresponse()
        raw = r.read(20000)
        conn.close()
        hdrs2 = dict((k.lower(), v) for k, v in r.getheaders())
        return r.status, hdrs2, raw
    except Exception as e:
        return -1, {}, repr(e).encode()


def main():
    for h in ["api.edition.in", "api-internal.edition.in"]:
        for path, extra in TESTS:
            st, hdrs, raw = req(h, path, extra)
            body = raw[:400].decode("utf-8", "replace")
            print("%-24s GET %-45s [%d] srv=%s ct=%s len=%d\n   body: %s" % (
                h, path, st, hdrs.get("server", "-"), hdrs.get("content-type", "-")[:30], len(raw), body.replace("\n", " ")), flush=True)
        # OPTIONS on gateway
        try:
            conn = http.client.HTTPSConnection(h, 443, timeout=10, context=ctx)
            conn.request("OPTIONS", "/gw/consumer/movies/v3/cities", headers={"User-Agent": UA, "Origin": "https://www.district.in",
                        "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization,content-type"})
            r = conn.getresponse()
            raw = r.read(2000)
            conn.close()
            hdrs2 = dict((k.lower(), v) for k, v in r.getheaders())
            print("%-24s OPTIONS gw [%d] allow=%s acao=%s acah=%s" % (h, r.status,
                hdrs2.get("allow", "-"), hdrs2.get("access-control-allow-origin", "-"), hdrs2.get("access-control-allow-headers", "-")), flush=True)
        except Exception as e:
            print("OPTIONS exc", repr(e)[:80], flush=True)
        print("", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
