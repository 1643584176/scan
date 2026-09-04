# -*- coding: utf-8 -*-
# _devsrv_routes1.py - enumerate dev server API routes with edge token
import sys, os, json, urllib.request, urllib.error

tok = json.load(open(r"D:\scan\netlify_report\_edge_tok.json"))["tok"]
DS_URL = "https://devserver-ar-6a98d6d818790895d7d5ac00--sec-b-08v4pk.netlify.app"

def req(method, url, timeout=15):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(4000)
            return resp.status, dict(resp.headers), b[:2000]
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(4000)[:1500]
    except Exception as ex:
        return -1, {}, str(ex)[:200]

paths = [
    "/", "/health", "/healthz", "/status", "/ping", "/api", "/api/", "/api/v1", "/v1",
    "/functions", "/functions/", "/.netlify/functions", "/.netlify/functions/",
    "/__netlify", "/__netlify/", "/.netlify", "/.netlify/",
    "/graphql", "/metrics", "/debug", "/info", "/version", "/version.json",
    "/files", "/fs", "/tree", "/browse", "/read", "/exec", "/run", "/shell",
    "/dev-server", "/dev_server", "/ds", "/server", "/runtime",
    "/openapi.json", "/swagger", "/docs", "/swagger.json",
    "/netlify", "/.netlify/status", "/.netlify/callback",
    "/favicon.ico", "/robots.txt",
    "/result", "/results", "/diff", "/.netlify/results.md",
    "/logs", "/log", "/stdout", "/stderr",
    "/env", "/environ", "/config", "/settings",
    "/sessions", "/agent", "/tasks",
]
seen = set()
for p in paths:
    if p in seen:
        continue
    seen.add(p)
    s, h, b = req("GET", DS_URL + p)
    bt = b.decode("utf-8", "replace") if isinstance(b, bytes) else str(b)
    bt = bt[:150].replace("\n", " ")
    tag = "HIT" if (s != 404 and "Route GET:" not in bt and "Route POST:" not in bt) else ""
    print("%-28s -> %-4s %s %s" % (p, s, h.get("Content-Type", ""), bt if tag else bt[:80]))
