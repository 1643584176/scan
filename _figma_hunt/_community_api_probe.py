"""community REST API 探测：用 A 会话 cookie 找 community 文件真实 fileKey"""
import subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK = open('cookie_header.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
CID = "1055785285964148921"

endpoints = [
    # community 详情/文件类
    f"https://www.figma.com/api/community/file/{CID}",
    f"https://www.figma.com/api/community/files/{CID}",
    f"https://www.figma.com/api/community/resource/{CID}",
    f"https://www.figma.com/api/community/resources/{CID}",
    # 搜索类
    "https://www.figma.com/api/community/search?query=pixelmatters&resource_type=file&page=1&page_size=20",
    "https://www.figma.com/api/community/files?query=pixelmatters",
    # thumbnail（原样 + 变体）
    f"https://www.figma.com/api/community/thumbnail?resource_type=file&resource_id={CID}&width=800&signature=fe8782f5-bee2-477c-8292-31cea3828676-cover",
    # embed
    f"https://www.figma.com/api/community/embed/{CID}",
    f"https://www.figma.com/community/thumbnail?resource_type=file&resource_id={CID}&width=800&signature=fe8782f5-bee2-477c-8292-31cea3828676-cover",
]

for u in endpoints:
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "-", "-w", "\n__HTTP_%{http_code}__%{size_download}__",
             "-H", f"Cookie: {CK}", "-H", f"User-Agent: {UA}",
             "-H", "accept: application/json,text/plain,*/*",
             "-H", "accept-language: zh-CN,zh;q=0.9",
             "-H", "referer: https://www.figma.com/community/file/1055785285964148921/design-system-template",
             u],
            capture_output=True, text=True, timeout=30)
        body = r.stdout
        code = body.rsplit("__HTTP_", 1)[-1].split("__", 1)[0] if "__HTTP_" in body else "?"
        size = body.rsplit("__HTTP_", 1)[-1].split("__", 2)[1] if "__HTTP_" in body else "?"
        content = body.rsplit("__HTTP_", 1)[0]
        print(f"\n=== {u}")
        print(f"    HTTP={code} size={size}")
        print(f"    {content[:500]}")
    except Exception as e:
        print(f"\n=== {u}\n    ❌ {e}")
