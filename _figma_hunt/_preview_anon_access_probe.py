# -*- coding: utf-8 -*-
"""generic_cached_preview 完整响应 + preview 站点匿名访问验证
核心问题:
 1. preview 完整响应(script_output_url 完整值)
 2. preview URL 匿名/带 token 访问返回什么(是否真能看到 A 的应用)
 3. 匿名重复请求确认非偶发
 4. A 的私有 design 文件(5Gs4PaTz11Hlk2sqVnidBG)是否也有 make preview(对照)
"""
import io, json, re, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_PRIV_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
GIT_URL = ("https://api.figma.com/git/make/file/2386353361958857999/public/code/"
           "7e8f327c-edcf-45e4-a11a-2a3d85c686c3.git")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def req(label, method, url, cookie=None, headers_extra=None, data=None, timeout=25):
    headers = {"User-Agent": UA, "Accept": "*/*", "Origin": BASE,
               "Referer": BASE + "/make/" + A_MAKE}
    if cookie:
        headers["Cookie"] = cookie
    if headers_extra:
        headers.update(headers_extra)
    r = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as res:
            raw = res.read().decode(errors='replace')
            print(f"[{label}] HTTP {res.status} ({len(raw)}B)")
            return res.status, raw, res.headers
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} ({len(raw)}B) {raw[:300]}")
        return e.code, raw, e.headers
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:150]}")
        return None, str(e), None


print("======== 1. preview 完整响应 (匿名) ========")
st, body, _ = req("匿名 preview", "GET",
                  f"{BASE}/api/make/{A_MAKE}/11%3A13/generic_cached_preview"
                  f"?git_repo_url={urllib.parse.quote(GIT_URL, safe='')}&git_ref=main")
print("完整响应:", body if st else "")

# 提取 preview url
m = re.search(r'"url":"(https://[^"]+)"', body or "")
script_m = re.search(r'"script_output_url":"(https://[^"]+)"', body or "")
preview_url = m.group(1) if m else None
script_url = script_m.group(1) if script_m else None
print("\npreview_url:", preview_url)
print("script_output_url:", script_url)

if preview_url:
    print("\n======== 2. preview 站点匿名访问 (带 token) ========")
    req("匿名 preview 站点", "GET", preview_url, timeout=30)
    print("\n======== 3. preview 站点不带 token ========")
    req("无 token", "GET", re.sub(r"\?__figma_cached_preview_token=.*$", "", preview_url), timeout=30)
    print("\n======== 4. preview 站点 B cookie + token ========")
    req("B+token", "GET", preview_url, cookie=BC, timeout=30)

if script_url:
    print("\n======== 5. script_output_url 匿名 ========")
    req("匿名 script output", "GET", script_url, timeout=30)

print("\n======== 6. 匿名重复请求 preview 元数据 (确认非偶发) ========")
for i in range(2):
    st, body2, _ = req(f"匿名 repeat {i+1}", "GET",
                       f"{BASE}/api/make/{A_MAKE}/11%3A13/generic_cached_preview"
                       f"?git_repo_url={urllib.parse.quote(GIT_URL, safe='')}&git_ref=main")

print("\n======== 7. A 私有 design 的 make preview (对照) ========")
req("匿名 私有design preview", "GET",
    f"{BASE}/api/make/{A_PRIV_DESIGN}/1%3A1/generic_cached_preview"
    f"?git_repo_url=x&git_ref=main")
