# -*- coding: utf-8 -*-
"""下载 event_subscriber chunk v2(2026-09-08)"""
import urllib.request

url = "https://hackerone.com/assets/static/event_subscriber-D6GKfWL_.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
    with open(r"D:\scan\h1kit\_h1x73_eventsub.js", "wb") as f:
        f.write(body)
    print(f"OK {len(body)} bytes")
except Exception as e:
    print("ERR", e)
