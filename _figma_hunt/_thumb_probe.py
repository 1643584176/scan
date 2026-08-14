"""thumbnail signature 校验测试 + REST 数字ID测试"""
import subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CK = open('cookie_header.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def probe(label, url, cookie=True, follow=False, extra=None):
    cmd = ["curl", "-s", "-D", "-", "-o", "/dev/null"]
    if cookie: cmd += ["-H", f"Cookie: {CK}"]
    cmd += ["-H", f"User-Agent: {UA}", "-H", "accept: */*"]
    if extra: cmd += extra
    if follow: cmd.append("-L")
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(f"\n=== {label}\n    {r.stdout[:900]}")

# 1. 换 resource_id（保持原 signature）→ signature 是否绑定 resource_id？
probe("换resource_id=9999999999 原signature", 
      "https://www.figma.com/community/thumbnail?resource_type=file&resource_id=9999999999&width=800&signature=fe8782f5-bee2-477c-8292-31cea3828676-cover")
# 2. 原 resource_id + 随机 signature → signature 是否校验？
probe("原resource_id 随机signature", 
      "https://www.figma.com/community/thumbnail?resource_type=file&resource_id=1055785285964148921&width=800&signature=00000000-0000-4000-8000-000000000000-cover")
# 3. 无 signature
probe("无signature", 
      "https://www.figma.com/community/thumbnail?resource_type=file&resource_id=1055785285964148921&width=800")
# 4. REST 数字 ID 作 key
probe("REST /api/files/1055785285964148921", 
      "https://www.figma.com/api/files/1055785285964148921")
# 5. hf_embed 页面（匿名）
probe("hf_embed 匿名", 
      "https://www.figma.com/file/1055785285964148921/hf_embed", cookie=False)
