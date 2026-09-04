# -*- coding: utf-8 -*-
# _ui_devservers2.py - find devServer REST path templates in API client chunk
import re, os

D = r"D:/scan/netlify_report/_js"
src = open(os.path.join(D, "net_7884.js"), encoding="utf-8", errors="replace").read()
print("size:", len(src))

# 1. literal path templates
for pat in (r'["\'][^"\']*dev[_-]?servers?[^"\']*["\']', r'["\'][^"\']*devServer[^"\']*["\']'):
    seen = set()
    for m in re.finditer(pat, src, re.I):
        s = m.group(0)
        if s in seen:
            continue
        seen.add(s)
        print("TPL:", s)

# 2. find definitions of methods named devServer/devServers: "devServer:function" style
print()
print("### method-like defs")
for m in re.finditer(r'([a-zA-Z_$][\w$]*):(?:async )?function[^}]{0,80}', src):
    pass

# find ".devServer=" or "devServer:(" patterns with following url
for m in re.finditer(r'(?:devServers?|activeDevServers|devServerHooks?|addDevServerHook|removeDevServerHook)\s*[:=]\s*(?:function)?[^,;]{0,200}', src):
    print("DEF:", m.group(0)[:220])
