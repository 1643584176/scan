# -*- coding: utf-8 -*-
"""考古:API token 管理 UI(settings 页)(2026-09-09)"""
import os
import re

# 在 app + 已下载 chunk 里找 api token 文案
files = [r"D:\scan\h1kit\_h1x4_app.js"]
chunk_dir = r"D:\scan\h1kit\_src_chunks"
if os.path.isdir(chunk_dir):
    files += [os.path.join(chunk_dir, f) for f in os.listdir(chunk_dir) if f.endswith(".js")]

pats = {
    "api_token_ui": r"(API token|ApiToken|api_token|personal access token|Access token)[^\"']{0,60}",
    "token_create": r"(createToken|generateToken|newApiToken|apiToken|api_token)\s*[:=(\[]",
    "token_page": r"(/settings/.*token|api_token_settings|token_settings)",
}
for fn in files:
    with open(fn, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
    for label, pat in pats.items():
        hits = set()
        for m in re.finditer(pat, data, re.I):
            ctx = data[max(0, m.start() - 60):m.start() + 60].replace("\n", " ")
            hits.add(ctx[:200])
        if hits:
            print(f"== {os.path.basename(fn)} [{label}] {len(hits)}")
            for h in list(hits)[:3]:
                print("   >", h)
