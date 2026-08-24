"""未测端点批量探测:A/B 双 cookie,找非 403/404 的异常响应
覆盖:code_connect in_context、figjam、users/batched、recent_prototypes、buzz_approvals、color_palettes、team_role_requests
"""
import sys, json, io, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
LK = "lk-a7138c76be6dcf31e2f25f4d3d33ca6a"  # Flowbite LK(已确认有效)

def probe(label, method, path, cookie, body=None):
    url = f"https://www.figma.com{path}"
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://www.figma.com",
         "Referer": "https://www.figma.com/", "Cookie": cookie}
    if body is not None:
        h["Content-Type"] = "application/json"
    try:
        r = requests.request(method, url, headers=h, json=body if body is not None else None,
                             timeout=20, allow_redirects=False)
        t = r.text
        flag = ""
        if r.status_code in (200, 201, 202):
            flag = " ★★★"
        elif r.status_code not in (403, 404):
            flag = " ★"
        print(f"[{label}] {method} {path} -> {r.status_code} ({len(t)}B){flag}")
        if flag:
            print(f"    {t[:500]}")
    except Exception as e:
        print(f"[{label}] {method} {path} -> ERR {type(e).__name__}: {str(e)[:60]}")

if __name__ == "__main__":
    print("======== 未测端点批量探测 ========")
    # code_connect in_context 系列(读路径)
    probe("A", "POST", "/api/code_connect/library/in_context/published_components", CK_A,
          body={"library_key": LK})
    probe("B", "POST", "/api/code_connect/library/in_context/published_components", CK_B,
          body={"library_key": LK})
    probe("A", "POST", "/api/code_connect/library/in_context/published_components/status", CK_A,
          body={"library_key": LK, "node_id": "14530:85888"})
    # figjam
    probe("A", "GET", "/api/figjam/default_collage_items", CK_A)
    probe("A", "GET", "/api/figjam/default_inserts", CK_A)
    # 用户/团队
    probe("A", "GET", "/api/users/batched?user_ids=1666382703778278399", CK_A)
    probe("A", "GET", "/api/recent_prototypes", CK_A)
    probe("A", "GET", "/api/team_role_requests", CK_A)
    # buzz_approvals(feature gate 检查)
    probe("B", "POST", "/api/buzz_approvals/create", CK_B, body={})
    probe("B", "POST", "/api/buzz_approvals/withdraw", CK_B, body={})
    probe("B", "POST", "/api/buzz_approvals/complete_v2", CK_B, body={})
    # color_palettes
    probe("A", "POST", "/api/color_palettes", CK_A, body={})
