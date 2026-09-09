# -*- coding: utf-8 -*-
"""sandbox contentType 变体 + resources/read 匿名行为(2026-09-09)"""
import urllib.request, urllib.error, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def req(url, label, method="GET", data=None, ctype=None):
    headers = dict(UA)
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else data.encode()
        headers["Content-Type"] = ctype or "application/json"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            b = resp.read().decode("utf-8", "replace")
            print(f"===== {label}\nHTTP {resp.status} len={len(b)} ctype={resp.headers.get('Content-Type')}")
            print(b[:500].replace("\n", " "))
    except urllib.error.HTTPError as e:
        b = e.read().decode("utf-8", "replace")
        print(f"===== {label}\nHTTP {e.code} len={len(b)}")
        print(b[:500].replace("\n", " "))
    except Exception as e:
        print(f"===== {label} ERR {e}")

B = "https://hackerone.com/hai/agentic_ui_mcp"
for ct in ["rawhtml", "html", "text", "json", "raw", "", "rawhtml/../../graphql", "%3Cscript%3E"]:
    req(f"{B}/sandbox?contentType={ct}", f"ct={ct or '(empty)'}")

# resources/read 匿名
req(f"{B}/resources/read", "read_anon_ui", method="POST",
    data='{"uri":"ui://prefab/app","organization_id":"gid://gitlab/Organization/1"}')
req(f"{B}/resources/read", "read_anon_http", method="POST",
    data='{"uri":"http://127.0.0.1/","organization_id":"x"}')
# 路径枚举
for p in ["", "/", "/sandbox", "/resources", "/resources/list", "/health", "/status"]:
    req(f"{B}{p}", f"path={p or '/'}")
