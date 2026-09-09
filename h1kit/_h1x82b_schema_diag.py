# -*- coding: utf-8 -*-
"""schema dump 诊断:看原始响应(2026-09-09)"""
import json
import urllib.request

BASE = "https://hackerone.com/graphql"
q = "{ __schema { types { name } } }"
data = json.dumps({"query": q}).encode()
req = urllib.request.Request(BASE, data=data, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json",
    "Accept": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("HTTP", r.status)
        body = r.read().decode("utf-8", "replace")
        print(body[:1500])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode("utf-8", "replace")[:1000])
except Exception as e:
    print("ERR", e)
