# -*- coding: utf-8 -*-
"""fuid 校验逻辑: 随机 fuid / 其他用户 fuid / 空 fuid 的权限判定
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def call(label, path, query=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:150]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:150]}")
        return e.code, raw


print("======== fuid 校验逻辑 (A 私有 design 文件) ========")
call("fuid=A(真实owner)", "/api/file_metadata/" + A_DESIGN, {"fuid": A_UID})
call("fuid=B(自己)", "/api/file_metadata/" + A_DESIGN, {"fuid": B_UID})
call("fuid=随机大数", "/api/file_metadata/" + A_DESIGN, {"fuid": "99999999999999999999"})
call("fuid=随机小数字", "/api/file_metadata/" + A_DESIGN, {"fuid": "12345"})
call("fuid=空字符串", "/api/file_metadata/" + A_DESIGN, {"fuid": ""})
call("fuid=A(大写/变形)", "/api/file_metadata/" + A_DESIGN, {"fuid": " 1666382703778278399"})

print("\n======== threads 接口 fuid 校验 ========")
call("threads fuid=A", "/api/ai_chat/threads",
     {"owner_id": A_DESIGN, "owner_type": "file", "fuid": A_UID})
call("threads fuid=随机", "/api/ai_chat/threads",
     {"owner_id": A_DESIGN, "owner_type": "file", "fuid": "99999999999999999999"})

print("\n======== X-Figma-User-ID 校验 ========")
import urllib.request as ur
for label, val in [("X-UID=A", A_UID), ("X-UID=随机", "99999999999999999999"), ("X-UID=空", "")]:
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC, "X-Figma-User-ID": val}
    try:
        req = ur.Request(BASE + "/api/file_metadata/" + A_DESIGN, headers=headers)
        with urllib.request.urlopen(req, timeout=25) as r:
            print(f"[X-UID={label}] HTTP {r.status} {r.read().decode(errors='replace')[:120]}")
    except urllib.error.HTTPError as e:
        print(f"[X-UID={label}] HTTP {e.code} {e.read().decode(errors='replace')[:120]}")
