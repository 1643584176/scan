"""HubSpot 登录：login/prep → login（base_pccp 测试账号）"""
import sys, json, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EMAIL = "base_pccp@protonmail.com"
PASSWORD = "Agent360User$5h2!QxR"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")

s = requests.Session()
s.headers.update({
    "User-Agent": UA,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Origin": "https://app.hubspot.com",
    "Referer": "https://app.hubspot.com/login",
})

# 1. 登录页（拿初始 cookie）
r0 = s.get("https://app.hubspot.com/login", timeout=20)
print("[1] GET /login ->", r0.status_code, "cookies:", list(s.cookies.keys()))

# 2. login/prep
r1 = s.post("https://app.hubspot.com/login-api/v1/login/prep?lb=app-api", timeout=20)
print("[2] POST login/prep ->", r1.status_code, r1.text[:400])

# 3. 实际登录
body = {"email": EMAIL, "password": PASSWORD, "rememberLogin": True}
r2 = s.post("https://app.hubspot.com/login-api/v1/login?lb=app-api",
            json=body, timeout=20)
print("[3] POST login ->", r2.status_code)
try:
    print("    resp:", json.dumps(r2.json(), ensure_ascii=False)[:800])
except Exception:
    print("    raw:", r2.text[:800])
