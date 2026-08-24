# -*- coding: utf-8 -*-
"""关键对照: B 新建的私有设计文件 canvas(.fig) 匿名下载测试
链路: versions(拿version_id) -> /version/{id}/canvas?fk=&fv=0 -> .fig
若匿名可下载私有文件 .fig => 严重权限错位
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
B_MAKE = "QooNP4ZnOkwGbudKlPX635"     # 公开 make 文件 (对照)
B_NEW = "ZKkMO8WDOMwRMwwWVmWYXO"      # 新建 design 文件 (私有?)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, url, cookie=None, follow=False):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    try:
        if follow:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                print(f"[{label}] HTTP {r.status} len={len(raw)} type={r.headers.get('Content-Type')}")
                return r.status, raw[:16]
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} :: {raw[:200]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} :: {raw[:200]}")
        return e.code, raw
    except Exception as e:
        print(f"[{label}] ERR {e}")
        return 0, str(e)


print("===== 1. 匿名 file_metadata: 新文件私有性 =====")
call("anon meta", f"{BASE}/api/files/{B_NEW}/file_metadata")
call("anon meta make", f"{BASE}/api/files/{B_MAKE}/file_metadata")

print("\n===== 2. 匿名 versions: 新文件 =====")
call("anon versions", f"{BASE}/api/versions/{B_NEW}?page_size=10")

print("\n===== 3. B versions: 新文件 (拿 version_id) =====")
st, raw = call("B versions", f"{BASE}/api/versions/{B_NEW}?page_size=10", cookie=BC)
vid = None
if st == 200 and raw.startswith("{"):
    try:
        d = json.loads(raw)
        vs = d["meta"]["versions"]
        print(f"  -> {len(vs)} versions")
        if vs:
            vid = vs[0]["id"]
            print(f"  -> version_id={vid}")
    except Exception as e:
        print("  parse err", e)

print("\n===== 4. 匿名 canvas 下载新文件 .fig (核心测试) =====")
if vid:
    call("anon canvas", f"{BASE}/version/{vid}/canvas?fk={B_NEW}&fv=0")
    call("anon canvas follow", f"{BASE}/version/{vid}/canvas?fk={B_NEW}&fv=0", follow=True)
    print("\n===== 5. B canvas 下载自己文件 (对照) =====")
    call("B canvas", f"{BASE}/version/{vid}/canvas?fk={B_NEW}&fv=0", cookie=BC, follow=True)
else:
    print("  无 version_id, 跳过")
