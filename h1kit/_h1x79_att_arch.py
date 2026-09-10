# -*- coding: utf-8 -*-
"""考古:附件 URL 域/路径形态 + 头像上传端点(2026-09-08)"""
import re

files = [r"D:\scan\h1kit\_h1x4_app.js", r"D:\scan\h1kit\_h1x3_main.js", r"D:\scan\h1kit\_h1x4_vendor.js"]
for fn in files:
    with open(fn, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
    # 附件/上传 URL 域
    for pat in [r"https://[a-z0-9.\-]*(user-content|attachments|usercontent|s3[^\"']*)[a-z0-9.\-]*",
                r"attachments/[A-Za-z0-9_\-\.]+", r"expiring_url"]:
        hits = set()
        for m in re.finditer(pat, data, re.I):
            hits.add(m.group(0)[:150])
        if hits:
            print(f"== {fn.split(chr(92))[-1]} [{pat}]")
            for h in list(hits)[:5]:
                print("   ", h)
    # avatar 上传 mutation 名
    for m in re.finditer(r"(updateAvatar|avatarUpload|uploadAvatar|changeAvatar|profileImage)[A-Za-z0-9_]*", data):
        pass
