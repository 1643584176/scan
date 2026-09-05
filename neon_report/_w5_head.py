# -*- coding: utf-8 -*-
for f in [r"F:\scan\neon_report\Neon-方向B-Beta新面测试闭合-20260905.md",
          r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"]:
    t = open(f, encoding="utf-8", errors="replace").read()
    print("=" * 40, f.split("\\")[-1], "len", len(t))
    for line in t.splitlines():
        s = line.strip()
        if s.startswith("#"):
            print("   ", s[:130])
    print()
