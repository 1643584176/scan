# -*- coding: utf-8 -*-
"""下载 agentic_ui_mcp_sandbox JS(2026-09-09)"""
import urllib.request, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
URL = "https://hackerone.com/assets/agentic_ui_mcp_sandbox-56d7dee5048f4d280b851ca599230ab11bc1914c5c1068a91af113eef2db12f3.js"
OUT = r"D:\scan\h1kit\_h1x131_sandbox.js"

req = urllib.request.Request(URL, headers=UA)
with urllib.request.urlopen(req, timeout=30) as r:
    body = r.read()
print("HTTP", r.status, "len:", len(body), "ctype:", r.headers.get("Content-Type"))
open(OUT, "wb").write(body)
print("saved:", OUT)
