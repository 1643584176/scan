"""Weave (app.weavy.ai) 匿名探测矩阵
目标：确定各端点认证要求 + 匿名可访问面
"""
import sys, json, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://app.weavy.ai"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def show(tag, r, show_body=True):
    body = r.text[:400].replace("\n", " ")
    print(f"[{tag}] {r.status_code} | {body}")

s = requests.Session()
H = {"User-Agent": UA, "Origin": "https://app.weavy.ai", "Referer": "https://app.weavy.ai/"}

print("===== 匿名 GET =====")
GETS = [
    "/v1/accounts:lookup",
    "/v1/users",
    "/v1/workspaces",
    "/v1/recipes/public",
    "/v1/node-definitions/public",
    "/v1/community/categories",
    "/v1/community/publisher-profiles",
    "/v1/models/prices",
    "/v1/figma-eligible-plans",
    "/v1/folders/list",
    "/v1/credits/window-status",
    "/v1/security/tier",
]
for p in GETS:
    try:
        r = s.get(BASE + p, headers=H, timeout=12)
        show(f"GET {p}", r)
    except Exception as e:
        print(f"GET {p} EXC {e}")

print("\n===== 匿名 POST =====")
POSTS = [
    ("/v1/accounts:lookup", {"idToken": "x"}),
    ("/v1/analytics/members-report", {"startDate": "2026-08-01"}),
    ("/v1/analytics/usage-report", {"startDate": "2026-08-01"}),
    ("/v1/token", {"grant_type": "refresh_token", "refresh_token": "x"}, "?key=AIzaSyC-qLy3TFyXMogJPfMkZJ9H_q46hEu1sx"),
    ("/v1/auth/figma/connections", None),
    ("/v1/workspaces/models/approve", {"modelIds": ["x"]}),
    ("/v1/users/onboarding-credits", {"force": True}),
]
for item in POSTS:
    p, body = item[0], item[1]
    qs = item[2] if len(item) > 2 else ""
    try:
        if body is None:
            r = s.post(BASE + p + qs, headers=H, timeout=12)
        else:
            r = s.post(BASE + p + qs, json=body, headers=H, timeout=12)
        show(f"POST {p}{qs}", r)
    except Exception as e:
        print(f"POST {p} EXC {e}")
