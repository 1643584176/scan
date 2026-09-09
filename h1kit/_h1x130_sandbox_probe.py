# -*- coding: utf-8 -*-
"""匿名探测 /hai/agentic_ui_mcp/sandbox 页面 + resources/read(2026-09-09)"""
import urllib.request, urllib.error, io, sys, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def get(url, label):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", "replace")
            print(f"===== {label}\nHTTP {r.status} len={len(body)} ctype={r.headers.get('Content-Type')}")
            print(body[:1200].replace("\n", " "))
            return body
    except urllib.error.HTTPError as e:
        b = e.read().decode("utf-8", "replace")
        print(f"===== {label}\nHTTP {e.code} len={len(b)}")
        print(b[:600].replace("\n", " "))
        return None
    except Exception as e:
        print(f"===== {label} ERR {e}")
        return None

get("https://hackerone.com/hai/agentic_ui_mcp/sandbox?contentType=rawhtml", "sandbox_rawhtml")
get("https://hackerone.com/hai/agentic_ui_mcp/sandbox", "sandbox_plain")
