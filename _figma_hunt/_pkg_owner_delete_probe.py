# -*- coding: utf-8 -*-
# 补测:published_package 删除是否存在归属/权限校验
# 矩阵:B 创建 -> A(owner)删  /  A 创建 -> B 删(复现)  /  清理
import requests, json, time, uuid

BASE = "https://www.figma.com"
FILE_KEY = "bv2nMIdFf4u3dESGail4sm"

def load_cookie(p):
    with open(p, encoding="utf-8") as f:
        # 多行 cookie 需合并为单行 header,否则 requests 报 missing_authentication
        return f.read().strip().replace("\n", "; ")

CK_A = load_cookie("ws_cookie_A_new.txt")
CK_B = load_cookie("ws_cookie_B_new.txt")

def headers(cookie):
    return {"Cookie": cookie, "Content-Type": "application/json"}

def create_pkg(cookie, identifier, ptype="npm"):
    body = {"package_identifier": identifier, "package_type": ptype}
    r = requests.post(f"{BASE}/api/files/{FILE_KEY}/published_package",
                      headers=headers(cookie), json=body, timeout=30)
    try:
        j = r.json()
    except Exception:
        j = r.text[:200]
    return r.status_code, j

def delete_pkg(cookie, pkg_id):
    r = requests.delete(f"{BASE}/api/files/{FILE_KEY}/published_package/{pkg_id}",
                        headers=headers(cookie), timeout=30)
    try:
        j = r.json()
    except Exception:
        j = r.text[:200]
    return r.status_code, j

def list_pkgs(cookie):
    r = requests.get(f"{BASE}/api/internal/livegraph/sinatra_resolver/component_browser_settings_sidebar_packages_navigation_stack_view?file_key={FILE_KEY}",
                     headers={"Cookie": cookie}, timeout=30)
    try:
        j = r.json()
    except Exception:
        return None
    try:
        return j.get("data", {}).get("file_v2", {}).get("published_packages", [])
    except Exception:
        return j

print("=== 0. 当前包列表(B视角) ===")
pkgs = list_pkgs(CK_B)
print("packages:", json.dumps(pkgs, ensure_ascii=False) if pkgs is not None else pkgs)

print("\n=== 1. B 创建包 pkg-owner-probe ===")
st, j = create_pkg(CK_B, "pkg-owner-probe", "npm")
print("B create:", st, json.dumps(j, ensure_ascii=False)[:300])

pkg_id = None
if isinstance(j, dict):
    pkg_id = j.get("id") or (j.get("data") or {}).get("id")
print("pkg_id:", pkg_id)

print("\n=== 2. A(owner) 删除 B 创建的包 ===")
if pkg_id:
    st, j = delete_pkg(CK_A, pkg_id)
    print("A delete B's pkg:", st, json.dumps(j, ensure_ascii=False)[:300])
else:
    print("skip: 拿不到包 id")

print("\n=== 3. A 创建包 pkg-owner-probe2 ===")
st, j = create_pkg(CK_A, "pkg-owner-probe2", "npm")
print("A create:", st, json.dumps(j, ensure_ascii=False)[:300])
pkg_id2 = j.get("id") if isinstance(j, dict) else None
print("pkg_id2:", pkg_id2)

print("\n=== 4. B 删除 A 创建的包(复现) ===")
if pkg_id2:
    st, j = delete_pkg(CK_B, pkg_id2)
    print("B delete A's pkg:", st, json.dumps(j, ensure_ascii=False)[:300])

print("\n=== 5. 清理:双方各自尝试删除剩余测试包 ===")
for ident in ["pkg-owner-probe", "pkg-owner-probe2"]:
    # 通过 livegraph 查 id
    pkgs = list_pkgs(CK_A)
    for p in (pkgs or []):
        if p.get("package_identifier") == ident:
            pid = p.get("id")
            for name, ck in [("A", CK_A), ("B", CK_B)]:
                st, j = delete_pkg(ck, pid)
                print(f"cleanup {ident} by {name}: {st}")
            break

print("\n=== 6. 最终状态确认 ===")
pkgs = list_pkgs(CK_A)
print("final packages:", json.dumps(pkgs, ensure_ascii=False) if pkgs is not None else pkgs)
