# -*- coding: utf-8 -*-
"""ET4: mcp-server auth shape probing + ticketnew /movies SPA surface"""
import http.client, ssl, re, json
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def req(h, method, path, headers=None, body=None, timeout=8):
    try:
        conn = http.client.HTTPSConnection(h, 443, timeout=timeout, context=ctx)
        hdrs = {"User-Agent": UA, "Accept": "*/*"}
        if headers:
            hdrs.update(headers)
        conn.request(method, path, body=body, headers=hdrs)
        r = conn.getresponse()
        raw = r.read(6000)
        conn.close()
        return r.status, dict((k.lower(), v) for k, v in r.getheaders()), raw[:3000]
    except Exception as e:
        return -1, {}, ("EXC " + repr(e)[:80]).encode()


def mcp_probe(tag, method, path, headers=None, body=None):
    st, hdrs, raw = req("mcp-server.zomato.com", method, path, headers, body)
    www = hdrs.get("www-authenticate", "-")[:100]
    print("%-28s [%d] www=%s body=%s" % (tag, st, www, raw[:220].decode("utf-8", "replace")), flush=True)


def main():
    print("== mcp-server auth shape ==", flush=True)
    mcp_probe("GET /mcp noauth", "GET", "/mcp")
    mcp_probe("GET /mcp Bearer=abc", "GET", "/mcp", {"Authorization": "Bearer abc123"})
    mcp_probe("GET /mcp X-Access-Token", "GET", "/mcp", {"X-Access-Token": "abc123"})
    mcp_probe("GET /mcp X-API-Key", "GET", "/mcp", {"X-API-Key": "abc123"})
    mcp_probe("POST /mcp noauth", "POST", "/mcp",
              {"Content-Type": "application/json"},
              json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2025-03-26",
                                     "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}))
    mcp_probe("POST /mcp Bearer=abc", "POST", "/mcp",
              {"Content-Type": "application/json", "Authorization": "Bearer abc123"},
              json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2025-03-26",
                                     "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}))
    for p in ["/.well-known/oauth-authorization-server", "/.well-known/openid-configuration",
              "/.well-known/mcp", "/health", "/healthz", "/status", "/version", "/info",
              "/metrics", "/favicon.ico", "/api", "/v1", "/v1/mcp", "/api/mcp", "/mcp/", "/sse",
              "/api/v1", "/graphql", "/admin", "/debug", "/docs/", "/redoc"]:
        mcp_probe("GET " + p, "GET", p)
    print("", flush=True)

    # ticketnew /movies SPA: grab page + locate next data / js bundle refs
    print("== ticketnew.com/movies ==", flush=True)
    st, hdrs, raw = req("ticketnew.com", "GET", "/movies", {"Accept": "text/html"})
    body = raw.decode("utf-8", "replace")
    print("status=%d len=%d" % (st, len(raw)), flush=True)
    # script src / link href / api hints
    for m in re.finditer(r'(?:src|href)="([^"]{5,180})"', body):
        u = m.group(1)
        if any(k in u for k in ("_next", "api", ".js", ".json")):
            print("REF:", u, flush=True)
    # inline __NEXT_DATA__ / self.__next
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', body, re.S)
    if m:
        try:
            d = json.loads(m.group(1))
            print("NEXT_DATA buildId=%s page=%s" % (d.get("buildId"), d.get("page")), flush=True)
            # runtimeConfig / props keys
            pg = d.get("props", {}).get("pageProps", {})
            print("pageProps keys:", list(pg.keys())[:30], flush=True)
        except Exception as e:
            print("NEXT_DATA parse exc", repr(e)[:100], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
