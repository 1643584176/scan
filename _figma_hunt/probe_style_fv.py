"""file_proxy style canvas + fv=checkpoint_token 测试

canvas 400 错误 "Invalid parameter for fv" → 需要 fv=checkpoint_token。
流程：
  1. /api/files/{key} 拿新鲜 checkpoint_token
  2. 登录态 + fv 请求 style canvas（应 200）
  3. 匿名 + fv 对照（若 200 = 匿名可拿私有样式数据）
"""
import json, sys, base64
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
CK = {c["name"]: c["value"] for c in SESS if c.get("name") and c.get("value")}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"}

FILE = "qzDqStIDJyGbthpKiuvfwg"
KEY = "c2f0e9a03b9f7ae6f69b24c8f620bc7839f5ed28"
VER = "N4l2fHwfqtsjBoJGQMXKc6"

# 1. 拿 checkpoint_token
r = requests.get(f"https://www.figma.com/api/files/{FILE}", cookies=CK, headers=UA, timeout=15)
j = r.json()
tok = j.get("checkpoint_token") or j.get("meta", {}).get("checkpoint_token")
print(f"/api/files 状态 {r.status_code}, checkpoint_token 前缀: {str(tok)[:60]}...")
if tok:
    try:
        print("  解码:", base64.b64decode(tok + "==").decode()[:160])
    except Exception as e:
        print("  解码失败:", e)

URLS = [
    f"/api/file_proxy/style/{KEY}/canvas?ver={VER}&fv={tok}",
    f"/style/{KEY}/thumbnail?ver={VER}&fv={tok}",
]


def test(url, cookies=None, save=None):
    try:
        r = requests.get("https://www.figma.com" + url, cookies=cookies, headers=UA, timeout=15)
        body = r.content
        info = f"{len(body)}B ct={r.headers.get('Content-Type','')}"
        if "json" in r.headers.get("Content-Type", ""):
            info += " " + body[:300].decode(errors="replace").replace("\n", " ")
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


print("\n=== 登录态 + fv（应 200） vs 匿名 + fv ===")
for u in URLS:
    print(f"\n{u}")
    b = test(u, CK, save="auth_style_fv.bin")
    a = test(u, save="anon_style_fv.bin")
    if a[0] == 200 and b[0] == 200 and a[1] != b[1]:
        print("  <<< 匿名 200 且内容不同 = 私有数据泄露!")
    elif a[0] == 200 and b[0] == 200 and a[1] == b[1]:
        print("  <<< 匿名 200 且内容相同（数据本就是公开的）")
