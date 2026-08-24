# -*- coding: utf-8 -*-
"""Weave git 仓库与 SCM 接口访问控制细节探测
线索: B(viewer) 打开 A 的 Weave 文件时拿到:
  git: https://api.figma.com/git/make/file/2386353361958857999/public/code/7e8f327c-....git
  plan: cc6b6125-a07f-4d39-a54c-50ef65f33919 (A 的 plan)
验证:
 1. git 仓库匿名 clone / 无权限访问是否可行
 2. scm/connections 的响应内容(B cookie / 匿名) —— 是否泄露 A 的 SCM 配置
 3. generic_cached_preview 的响应(B / 匿名)
 4. 对比: A 的私有文件(5Gs4PaTz11Hlk2sqVnidBG)关联的 make git 是否存在
"""
import io, json, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
API = "https://api.figma.com"
GIT_URL = ("https://api.figma.com/git/make/file/2386353361958857999/public/code/"
           "7e8f327c-edcf-45e4-a11a-2a3d85c686c3.git")
PLAN_ID = "cc6b6125-a07f-4d39-a54c-50ef65f33919"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_PRIV_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


AC = load('ws_cookie_A_new.txt')
BC = load('ws_cookie_B_new.txt')


def call(label, method, url, cookie=None, headers_extra=None, data=None, timeout=25):
    headers = {"User-Agent": UA, "Accept": "*/*", "Origin": BASE,
               "Referer": BASE + "/make/" + A_MAKE}
    if cookie:
        headers["Cookie"] = cookie
    if headers_extra:
        headers.update(headers_extra)
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} ({len(raw)}B)")
            print(f"  ↳ {raw[:600]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} ({len(raw)}B)")
        print(f"  ↳ {raw[:400]}")
        return e.code, raw
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:120]}")
        return None, str(e)


print("======== 1. git 仓库匿名访问 (无 cookie) ========")
call("匿名 git info/refs", "GET", GIT_URL + "/info/refs?service=git-upload-pack")

print("\n======== 2. git 仓库 B cookie ========")
call("B git info/refs", "GET", GIT_URL + "/info/refs?service=git-upload-pack", cookie=BC)

print("\n======== 3. git 仓库 A cookie ========")
call("A git info/refs", "GET", GIT_URL + "/info/refs?service=git-upload-pack", cookie=AC)

print("\n======== 4. scm/connections (B cookie, A plan) ========")
call("B→A plan scm", "GET",
     f"{BASE}/api/plans/{PLAN_ID}/scm/connections?ugit_url=" + urllib.parse.quote(GIT_URL, safe=''),
     cookie=BC)

print("\n======== 5. scm/connections (匿名) ========")
call("匿名 scm", "GET",
     f"{BASE}/api/plans/{PLAN_ID}/scm/connections?ugit_url=" + urllib.parse.quote(GIT_URL, safe=''))

print("\n======== 6. generic_cached_preview (B cookie) ========")
call("B preview", "GET",
     f"{BASE}/api/make/{A_MAKE}/11%3A13/generic_cached_preview"
     f"?git_repo_url={urllib.parse.quote(GIT_URL, safe='')}&git_ref=main",
     cookie=BC)

print("\n======== 7. generic_cached_preview (匿名) ========")
call("匿名 preview", "GET",
     f"{BASE}/api/make/{A_MAKE}/11%3A13/generic_cached_preview"
     f"?git_repo_url={urllib.parse.quote(GIT_URL, safe='')}&git_ref=main")
