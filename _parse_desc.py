# -*- coding: utf-8 -*-
"""本地: 解压 proto rawDesc 拿 SpawnRequest 字段名"""
import gzip, re, io

d = open("_sandbox_init_new.bin", "rb").read()

# 1) 找 gzip magic
hits = [m.start() for m in re.finditer(rb"\x1f\x8b\x08", d)]
print("gzip magic hits:", len(hits), [hex(h) for h in hits[:20]])

# 2) 逐个解压, 找含 spawn 字段名的
for h in hits:
    try:
        raw = gzip.decompress(d[h:h+0x10000])
    except Exception:
        continue
    if b"command" in raw or b"SpawnRequest" in raw or b"workingDirectory" in raw:
        print("=== gzip @%#x decompressed %d bytes ===" % (h, len(raw)))
        # 提取可读字符串
        for m in re.finditer(rb"[a-zA-Z][a-zA-Z0-9_]{2,30}", raw):
            print("  %r" % m.group().decode())
        break
else:
    # 3) 未压缩 rawDesc: 直接搜字符串 "spawn.spawn" 或字段模式
    print("no gzip hit, searching plain")
    for pat in [rb"workingDirectory", rb"SpawnRequest", rb"processId"]:
        for m in re.finditer(pat, d):
            s = max(0, m.start()-0x100)
            ctx = d[s:m.start()+0x200]
            print("--- %r @%#x ---" % (pat, m.start()))
            for mm in re.finditer(rb"[a-zA-Z][a-zA-Z0-9_]{2,30}", ctx):
                print("  %r" % mm.group().decode())
            break
