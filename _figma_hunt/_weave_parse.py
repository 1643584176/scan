import sys, io, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
src = io.open('weave_home.html', encoding='utf-8', errors='replace').read()
scripts = re.findall(r'<script[^>]*src="([^"]+)"', src)
print("=== scripts ===")
for s in scripts[:15]:
    print(" ", s)
apis = re.findall(r'["\'](/api/[^"\']{3,80})["\']', src)
print("\n=== api 路径 ===")
for a in sorted(set(apis))[:25]:
    print(" ", a)
doms = sorted(set(re.findall(r'https?://([a-z0-9.\-]*figma[a-z0-9.\-]*)', src)))
print("\n=== figma 域名 ===")
for d in doms[:15]:
    print(" ", d)
