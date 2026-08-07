# -*- coding: utf-8 -*-
"""POST-only 接口无认证探测：区分"认证在方法层之前"vs"无认证触达业务层"
对 GET 405 的接口族发 POST，观察 401(有认证) / 400(无认证但缺参) / 200(无认证可调用) / 其他
"""
import requests, json, sys, re, urllib3
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://wolt.com",
    "Accept": "application/json",
    "X-HackerOne-Research": "pccp",
}

# (域, 路径, body 候选)
TARGETS = [
    # restaurant-api（waw-api 企业端 POST-only 接口）
    ("restaurant", "/v1/waw-api/corporate-leads", [None, {"email": "a@a.com"}, {}]),
    ("restaurant", "/v1/waw-api/corporates/1/restricted", [None, {"corporate_id": 1}, {}]),
    ("restaurant", "/v1/group_order/", [None, {}]),
    ("restaurant", "/v1/opstools/users/search", [{"q": "a"}, {"query": "a"}, {"email": "a@a.com"}]),
    ("restaurant", "/v1/users/start_email_verification", [None, {"email": "a@a.com"}]),
    ("restaurant", "/v1/subscriptions", [None, {}]),
    ("restaurant", "/v1/corporates", [None, {}]),
    ("restaurant", "/v1/group_order/guest/join/1", [None, {}]),
    ("restaurant", "/v1/group_order/{id}/locked", [None, {}]),
    ("restaurant", "/v1/group_order/{id}/invite/{id}", [None, {}]),
    ("restaurant", "/v1/group_order/{id}/participants/me", [None, {}]),
    ("restaurant", "/v1/group_order/{id}/participants/me/basket", [None, {}]),
    ("restaurant", "/v1/group_order/guest/{id}/participants/me", [None, {}]),
    ("restaurant", "/v1/group_order/guest/{id}/referral_code", [None, {}]),
    ("restaurant", "/v1/waw-api/corporates/{id}/cx-purchases/{id}", [None, {}]),
    ("restaurant", "/v1/waw-api/corporates/{id}/purchases/{id}", [None, {}]),
    # consumer-api
    ("consumer", "/v1/access_confirmation/1/submit", [None, {}]),
    ("consumer", "/v1/access_confirmation/status", [None, {"phone_number": "+358000000000"}]),
    ("consumer", "/v1/delivery-orders/1/cancel", [None, {}]),
    ("consumer", "/v2/delivery/info", [None, {}]),
    ("consumer", "/v2/delivery/info/1", [None, {}]),
    ("consumer", "/v1/utils/send-email", [None, {"to": "a@a.com", "subject": "t", "body": "b"}]),
    ("consumer", "/v2/notifications/1/seen", [None, {}]),
    ("consumer", "/v1/admin/seven-eleven/taskboard-zipcodes/upload", [None, {}]),
    ("consumer", "/v1/admin/seven-eleven/taskboard-zipcodes/delete", [None, {}]),
    ("consumer", "/v1/wauth2/access_token", [{"username": "a@a.com", "password": "x"}]),
    ("consumer", "/v1/wauth2/login_methods/1/verify", [None, {}]),
    ("consumer", "/order-xp/v1/baskets/bulk/delete", [None, {}]),
    ("consumer", "/v1/log", [None, {}]),
    ("consumer", "/v1/user/1/verify_email", [None, {}]),
    ("consumer", "/v1/users/me/settings", [None, {}]),
]

BASES = {"consumer": "https://consumer-api.wolt.com", "restaurant": "https://restaurant-api.wolt.com"}

print(f"{'#':<3}{'BASE':<11}{'PATH':<60}{'BODY':<22}{'ST':<5}SNIPPET")
print("=" * 130)
out = []
for i, (bname, p, bodies) in enumerate(TARGETS):
    base = BASES[bname]
    p_real = p.replace("{id}", "1")
    for body in bodies:
        try:
            if body is None:
                r = requests.post(base + p_real, headers=H, timeout=8, verify=False)
            else:
                # 先 JSON，若 415 再 form
                r = requests.post(base + p_real, headers=H, json=body, timeout=8, verify=False)
                if r.status_code == 415:
                    r = requests.post(base + p_real, headers={**H, "Content-Type": "application/x-www-form-urlencoded"}, data=body, timeout=8, verify=False)
        except Exception as e:
            print(f"{i:<3}{bname:<11}{p_real[:58]:<60}{str(body)[:20]:<22}{'ERR':<5}{str(e)[:60]}")
            continue
        snip = r.text.replace("\n", " ")[:130]
        print(f"{i:<3}{bname:<11}{p_real[:58]:<60}{str(body)[:20]:<22}{r.status_code:<5}{snip}")
        out.append({"base": bname, "p": p_real, "body": body, "st": r.status_code, "snip": snip, "len": len(r.text)})

json.dump(out, open(r"D:\scan\_wolt_hunt\_api_post_unauth.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\nDONE")
