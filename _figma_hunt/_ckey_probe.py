"""测试 checkpoint key 5h8vKLfD3ItG0RxCGIUHuf 是否可作为 fileKey"""
import subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CK = open('cookie_header.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def probe(label, url, cookie=True):
    cmd = ["curl", "-s", "-o", "-", "-w", "\n__HTTP_%{http_code}__%{size_download}__",
           "-H", f"User-Agent: {UA}", "-H", "accept: */*"]
    if cookie: cmd += ["-H", f"Cookie: {CK}"]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    body = r.stdout
    parts = body.rsplit("__HTTP_", 1)
    code, size = (parts[-1].split("__", 1) if len(parts) > 1 else ("?", "?"))
    content = parts[0] if len(parts) > 1 else body
    print(f"\n=== {label}")
    print(f"    HTTP={code} size={size}")
    print(f"    {content[:600]}")

CKPT = "5h8vKLfD3ItG0RxCGIUHuf"
probe(f"REST /api/files/{CKPT} (匿名)", f"https://www.figma.com/api/files/{CKPT}", cookie=False)
probe(f"REST /api/files/{CKPT} (A会话)", f"https://www.figma.com/api/files/{CKPT}")
probe(f"REST /api/community/thumbnail?resource_type=file&resource_id={CKPT}", 
      f"https://www.figma.com/community/thumbnail?resource_type=file&resource_id={CKPT}&width=800", cookie=False)
