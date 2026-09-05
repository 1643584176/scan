# -*- coding: utf-8 -*-
"""ET5: full MCP oauth metadata + ticketnew/district JS bundle endpoint extraction"""
import http.client, ssl, re, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def get(h, path, headers=None, maxread=200000):
    conn = http.client.HTTPSConnection(h, 443, timeout=12, context=ctx)
    hdrs = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    conn.request("GET", path, headers=hdrs)
    r = conn.getresponse()
    raw = r.read(maxread)
    conn.close()
    return r.status, dict((k.lower(), v) for k, v in r.getheaders()), raw


def main():
    print("== MCP well-known full ==", flush=True)
    for p in ["/.well-known/oauth-authorization-server", "/.well-known/openid-configuration"]:
        st, hdrs, raw = get("mcp-server.zomato.com", p)
        print("--- %s [%d] ---" % (p, st), flush=True)
        print(raw.decode("utf-8", "replace")[:4000], flush=True)

    print("\n== ticketnew.com/movies full html ==", flush=True)
    st, hdrs, raw = get("ticketnew.com", "/movies", {"Accept": "text/html"})
    body = raw.decode("utf-8", "replace")
    print("status=%d total_len=%d ct=%s" % (st, len(raw), hdrs.get("content-type", "")), flush=True)
    # collect all script src + next data
    srcs = re.findall(r'<script[^>]+src="([^"]+)"', body)
    for s in srcs:
        print("JS:", s, flush=True)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', body, re.S)
    if m:
        try:
            d = json.loads(m.group(1))
            print("NEXT buildId=%s page=%s" % (d.get("buildId"), d.get("page")), flush=True)
            pg = d.get("props", {}).get("pageProps", {})
            s = json.dumps(pg)
            print("pageProps(%d): %s" % (len(s), s[:1500]), flush=True)
        except Exception as e:
            print("NEXT parse exc %s" % repr(e)[:120], flush=True)
    else:
        # maybe react-root shell; dump tail
        print("no NEXT_DATA; html head:", body[:800].replace("\n", " "), flush=True)

    print("\n== district.in homepage ==", flush=True)
    st, hdrs, raw = get("www.district.in", "/", {"Accept": "text/html"})
    body = raw.decode("utf-8", "replace")
    print("status=%d len=%d" % (st, len(raw)), flush=True)
    srcs = re.findall(r'<script[^>]+src="([^"]+)"', body)
    for s in srcs[:15]:
        print("JS:", s, flush=True)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', body, re.S)
    if m:
        try:
            d = json.loads(m.group(1))
            print("NEXT buildId=%s page=%s" % (d.get("buildId"), d.get("page")), flush=True)
        except Exception as e:
            print("parse exc", repr(e)[:80], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
