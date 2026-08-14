# Figma livegraph 管理级探测 · 测试结论（2026-08-10）

## 一、测试目标

验证两条假设（SUMMARY.md 后续方向 2/3）：

1. livegraph WS 的 FileBrowser*/CurrentTeamCombinedPermissions 等 view 是否可跨 teamId/orgId 越权
2. 管理级 view（orgAdminUsers / plan_ai_usage_by_users_v2 / user_group_members / unclaimed_domain_users / admin_request_dashboard）及 HTTP pagination_resolver/sinatra_resolver 系列是否对普通账号可达

## 二、测试资产（A 账号新鲜会话）

- 会话：浏览器抓取的真实 livegraph URL（含完整 preload + 3 个真实 viewHash）+ 全新 cookie
- cookie 文件：`ws_cookie_latest.txt`（旧备份 `ws_cookie_latest_old.bak`）
- 身份：userId=1666382703778278399（A 账号），authSuccess 通过
- teamId：A=1666382706663462213，B=1666397394890946753（B 账号），随机=9999999999999999999
- 真实 viewHash（来自浏览器 preload）：
  - FileBrowserSidebarData = 19ed18eb...
  - CurrentTeamCombinedPermissions = f25ed3ec...
  - FileBrowserPaginatedRecentFilesView = c60c9c1b...

## 三、WS 矩阵结果（test_fresh_preload.py）

### 基线（真实 hash + 真实 args）→ 全部正常返回数据

| view | args | 结果 |
|---|---|---|
| FileBrowserPaginatedRecentFilesView | action=view, firstPageSize=25 | ✅ RecentFile2 ×5（A 最近文件） |
| CurrentTeamCombinedPermissions | teamId=TEAM_A | ✅ TeamPublicInfo/Team/TeamLimitedInfo（"1643584176's team"） |
| FileBrowserSidebarData | currentTeamId=TEAM_A | ✅ 14 类型，initial=9（A 收藏/分区/团队） |

### 机制发现：preload 由服务端注册，hash 不被校验

- 对 preload 已注册的 view 用**相同 args 重复订阅** → `duplicate-subscribe-attempt-with-same-arguments`（真实 hash 与零 hash 均触发，说明按 args 判重，hash 无关）
- 用"为 A 队 args 计算的 hash"订阅 **B 队 args** → 无 hash 错误，正常处理
- **结论：viewHash 是纯客户端缓存键，服务端不校验。此前"失败是否因 hash"的歧义排除。**

### 越权注入（真实 hash + B 队/随机 teamId）→ 无泄漏

| 订阅 | B 队/随机结果 |
|---|---|
| CurrentTeamCombinedPermissions teamId=TEAM_B | ⚠️ 查询键存在但 initial 全部为空（权限过滤） |
| CurrentTeamCombinedPermissions teamId=随机 | no-data（同空） |
| FileBrowserSidebarData currentTeamId=TEAM_B | ⚠️ 仅返回 A 自己数据（currentUser/org 键），无 B 资源 |
| FileBrowserSidebarData currentTeamId=随机 | 同上 |

证据文件：`cross_team_out/fresh_perms_B_realhash.json`（B 队键全空）、`fresh_sidebar_B_realhash.json`（仅 A 自身键）。

### 管理级 view → 注册表缺失（WS 通道封死）

| view | 真实 hash | 零 hash |
|---|---|---|
| orgAdminUsers | view-does-not-exist | view-does-not-exist |
| plan_ai_usage_by_users_v2 | view-does-not-exist | view-does-not-exist |
| user_group_members | view-does-not-exist | view-does-not-exist |
| unclaimed_domain_users | view-does-not-exist | view-does-not-exist |
| admin_request_dashboard | view-does-not-exist | view-does-not-exist |

- 错误信息：`Attempted to subscribe to view <name> that does not exist`
- 与 duplicate 错误（view 存在）并存 → 注册表机制正常，管理 view 不在 livegraph view 注册表中，与权限无关

## 四、HTTP 管理面结果（probe_internal_fresh.py，A 登录态）

25 个端点（pagination_resolver 15 + sinatra_resolver 10），orgId 用 TEAM_A 与公开 org 对照：

- **全部 403 Forbidden**（含自己 orgId 的 org_admin / plan_ai_usage / user_group_members 等）
- 结论：管理面 HTTP 端点对非管理员整体拒绝，无参数差异可利用

## 五、结论

1. **排除**：管理级数据（WS view + HTTP endpoint）对普通账号均不可达 → "非管理员拉组织管理数据"假设系统性排除
2. **排除**：teamId/currentTeamId 跨队注入在真实 view 上不泄漏 → 服务端按认证会话用户过滤
3. **确认机制**：livegraph viewHash 不参与服务端校验；preload 参数由服务端注册订阅
4. 边界说明：以上为 A 账号单侧结论；B 账号对称验证未做（B cookie 已过期）；"无越权痕迹不等于无越权可能"，仅限本次注册表/会话

## 六、脚本与证据索引

| 文件 | 用途 |
|---|---|
| test_fresh_preload.py | WS 矩阵（真实 preload URL） |
| probe_internal_fresh.py | HTTP 管理端点探测 |
| ws_cookie_latest.txt | A 账号新鲜 cookie（备份 ws_cookie_latest_old.bak） |
| cross_team_out/fresh_*.json | 各 case 原始 mutations（基线有数据，B 队全空） |
| cross_team_out/perms_*.json / sidebar_*.json | 8-10 旧会话对照（同结论） |

## 七、后续方向（候选）

1. B 账号对称验证（需用户重新抓 B 账号 livegraph URL）
2. 其他攻击面：公开文件 key 枚举基线（OpenEditorFileData）、fuid 参数、FileBrowserTeamPageFolderItemsView folder 级注入（旧结论待重跑）
3. Weave 域名（scope 新成员）越权面
