# Figma H1 赏金测试 · 进度整理

更新日期：2026-08-11

## 项目信息

- 平台：HackerOne（hackerone.com/figma），Managed，$50 minimum
- 官方重点：high/critical findings
- Scope 8 项：www.figma.com、api.figma.com、Figma for Jira、Desktop App、iOS/Android、Slack App、Teams App、Figma Weave（原 Weavy，figma.com/weave/*）
- 注意：Weave 为 2026-07-07 新加入 scope，值得优先探索（weave_home.html 已抓取）

## 测试账号

| 用途 | 邮箱 | 说明 |
|---|---|---|
| 新测试账号 | 729488839@qq.com | 2026-08-07 启用，login.py 已切换 |
| 旧测试账号 | 1643584176@qq.com | 同密码，已登录过 |

- 凭据仅存于 login.py 脚本（密码不写入记忆/文档）
- figma_session.json 为旧账号 session，新账号登录后覆盖

## 已完成侦察（2026-08-07 上午）

### 匿名态（anon_capture2.json）
- 159 个请求捕获：file_metadata、files/batch、files/{key}/realtime_token、versions/{key}、resources、plugins/batch、design_systems/libraries_by_library_keys、user/plans、authed_users/plans、v2/statsig/bootstrap 等 23 个 API
- 2 条 livegraph WS + 461 帧（auth 消息 userId=null 匿名态）
- 匿名可访问文件：bv2nMIdFf4u3dESGail4sm（公开 file）

### 登录态（ws_traffic.json / ws_url_fresh.txt）
- livegraph WS 认证成功：authSuccess userId=1666382703778278399（旧账号）
- WS URL 带 preload 参数：FileBrowserSidebarData、CurrentTeamCombinedPermissions、FileBrowserPaginatedRecentFilesView 等查询（teamId=166638270706663462213）

### JS chunk 提取
- chunk_urls.txt：69 个（主页/files 页）
- chunk_urls_editor.txt：106 个（editor 页）
- chunk_urls_community.txt：空（community 域名未抓到）

### 接口清单（editor_apis.txt，216 个 /api/ 路径）
- cortex 系列（AI）：/api/cortex/assistant/*、/api/cortex/design/editor_ai/*（clipdrop 等）、/api/cortex/design/first_draft/*、/api/cortex/dev/* 等
- livegraph pagination_resolver 系列：/api/internal/livegraph/pagination_resolver/*（admin_request_dashboard、plan_ai_usage_by_users、org_*、user_group_members 等，疑似管理员/组织内部查询）
- 其他：figment-proxy、file_proxy/brushes、agentcontrol/subscribe、integrations/supabase/authorize

## 工具链

- login.py：Playwright 自动登录（处理 AWS WAF challenge），输出 figma_session.json
- api_client.py：从 figma_session.json 加载 cookie 的已登录 requests 客户端，`python api_client.py [session.json]` 验证 /api/user
- 使用方式：先跑 login.py 获取新 session → api_client.py 验证 → 基于 editor_apis.txt / anon reqs 做已登录接口测试

## 后续方向（待确认）

1. ✅ 已完成（2026-08-10）：livegraph preload 跨 teamId 越权 → **无泄漏**，详见 [livegraph_admin_probe_结论.md](livegraph_admin_probe_结论.md)
2. ✅ 已完成（2026-08-10）：pagination_resolver 系列权限校验 → **全部 403**（非管理员整体拒绝）
3. 待办：B 账号对称验证（需重抓 B 账号 livegraph URL）
4. 待办：公开文件 key 枚举基线（OpenEditorFileData）、fuid 参数、FileBrowserTeamPageFolderItemsView folder 级注入重跑
5. ❌ 已放弃（2026-08-11）：Weave 面（详见下方「Weave 侦察记录（已封存）」）

## Weave 侦察记录（已封存 2026-08-11）

**放弃原因**：登录链路无法打通（OAuth code 一次性且有效期极短、api.weavy.ai POST 被 Cloudflare WAF 拦需完整浏览器头、app.weavy.ai 用户浏览器访问不稳定），无法获取登录态 Bearer token，登录面 IDOR 无法开展。

**已有发现（可后续复用）**：
- scope 原文确认：Figma Weave (formerly Weavy)，入口 = Figma 应用内 iframe 或 **https://weavy.ai**（含 app.weavy.ai / api.weavy.ai / weave.figma.com，均在 scope 内）
- weave.figma.com / www.figma.com/weave/ 均 404 废弃；官网菜单指向 https://weave.figma.com（营销站）
- 产品本体：app.weavy.ai（Netlify Next.js SPA），API 域 api.weavy.ai/api，主 bundle index-i3HM40rF.js（weavy_bundle.js 5.8MB）
- 109 个 /v1/ 端点：accounts/analytics/auth/figma/folders/projects/recipes/models/community/credits 等
- 认证机制：Figma OAuth（client_id=SbBGdDK0JIYzSU92FsIHQr，redirect=app.weavy.ai/signin|settings，scope=openid profile email file_content:read file_create）→ /v1/auth/figma/oidc/token 换 id_token → Firebase OAuthProvider(oidc.figma) 换 Bearer
- 匿名面：统一 401（internalErrorCode=1001），无匿名/邮箱注册面；POST /v1/auth/figma/oidc/token 需完整浏览器头过 WAF
- 关键文件：weavy_bundle.js、_weavy_anon_probe.py、_weavy_exchange.py（code→token 交换）、weavy_idtoken.json、weavy_oauth_state.json

## 关键机制结论（2026-08-10）

- livegraph viewHash 是纯客户端缓存键，**服务端不校验**（真实/零 hash 行为一致；跨 args 复用 hash 不报错）
- preload 参数由服务端注册订阅，同 args 重复订阅 → duplicate-subscribe 错误
- 管理级 view（orgAdminUsers 等）在 livegraph 注册表中**不存在**（view-does-not-exist，与权限无关）
- 跨 teamId 注入（CurrentTeamCombinedPermissions/FileBrowserSidebarData）→ 服务端按会话用户过滤，B 队/随机 teamId 返回空或回退自身数据

## 2026-08-19 测试记录

### app_auth 桌面授权链（create→grant→redeem）→ 安全闭环
- 端点：POST /api/session/app_auth（create，body={app_type}）、POST /api/session/app_auth/{aid}/grant、POST /api/session/app_auth/redeem（body={g_secret}）、GET /app_auth/{aid}/grant（页面）、POST /api/session/clear_cont
- 流程（JS 2285 chunk 确认）：桌面应用 create → 浏览器 GET grant 页面 → 页面 POST grant（仅带 X-Figma-User-ID 头）→ 页面调 clear_cont → unsafeRedirect(figma://app_auth/redeem?g_secret=X) → 桌面应用 main.js tryHandleAppAuthRedeemURL 拦截 → postMessage redeemAppAuth → 页面 POST /api/session/app_auth/redeem
- **create 匿名可用**（200，aid 随机 UUID，无危害）
- **grant 强校验**：① X-Figma-User-ID↔authn cookie 绑定（纯净 B cookie claim A_UID → 401 空 message；B cookie 含 A token 时成功是多账号正常行为）② 创建会话校验（A cookie 对 B 创建的 aid grant → 400；创建者本人 grant → 200）
- **grant 页面不泄露 g_secret**：A/匿名 GET B 的 aid 页面均无 g_secret（payload 有 app_auth_users 按访问者渲染）
- **redeem 400 根因未明**：脚本无法复现成功（偶发一次 202 空 body 无法稳定复现）；grant/create 响应的 grantor_session_id 均为 null；tsid 为纯客户端随机值（模块 657352）不校验；疑似需真实浏览器会话上下文（grantor session），需浏览器抓包才能确认，不影响安全结论
- 真实 aid 3d3d226e 已 404（消费后删除）；figma.session 中 grant URL 证明用户真实桌面流程 redeem 成功
- 结论：无跨用户伪造/泄露/劫持面，安全

### .fig 源文件下载权限（canvas/versions/checkpoint）→ 安全
- versions API：A 私有 make 文件 5zb5YkoxMa09KpqOyuLcHD 匿名/B→403，A owner→200；公开 make 文件匿名→200（含 checkpoint_path，公开预期）
- /version/{vid}/canvas?fk=&fv=0：匿名 404 / B 404 / A owner 200 binary/octet-stream（.fig 源文件）
- checkpoint 直链（static.figma.com / s3-alpha-sig.figma.com）：403/404（需签名 URL）
- 结论：私有文件源文件下载权限门完整，无越权

### 其它线 → 安全
- Figma for Jira JWT（figma-for-jira.figma.com/auth/checkAuth）：alg:none/弱密钥/随机 iss/缺字段/过期/畸形 全 401，校验严格
- feed 发帖端点：404（路径不存在）
- feed resolver 跨 uid/org 注入：全 403
- GitHub 集成 .git 仓库直链：401 authentication required
- team role_requests：403；users/batched：公开（已知）
- mcp session_token_exchange：202（响应正常）

### 2026-08-19 续：livegraph / cortex / user-state 线（web 端）→ 全部安全闭环

**多账号 cookie 污染关键发现**：ws_cookie_B_new.txt 的 `__Host-figma.authn` 和 `__Host-figma.embed` 均含 A+B 双 token（B 浏览器多账号登录）。
任何 B 伪装 A 的测试必须用**纯净 cookie**：
- `make_pure`：authn 只留目标 uid
- `make_abs_pure`：authn+embed 都只留目标 uid（embed 是第二身份载体，曾导致 FileByKey 假阳性：纯净 B+claim A 读到 A 私有文件元数据实为 embed 残留）

| 测试线 | 方法 | 结论 |
|---|---|---|
| livegraph userId 伪造 | 绝对纯净 B cookie + auth claim A | **安全**：claim 身份必须 ∈ cookie token 集合，否则 authUserId=None 拒绝 |
| FileByKey 跨文件读 | 纯净 B+claim A 订阅 FileByKey | **安全**：embed 清空后 403/空壳 |
| FileCustomToolsMetadataView + __requestId | 4 组对照 | **安全**：401 userId 语义与 claim 身份一致，权限门存在 |
| cortex X-Figma-User-ID 伪造 | B cookie+claim A→200(多账号)；A cookie+claim B→403 | **安全**：header↔cookie 绑定强校验；改 authn 后 mac 失效→401 |
| weave run/inspect | B 对 A 文件 | **安全**：文件权限校验 403 |
| /api/livegraph/view | FileByKey 直连 | **安全**：白名单外 not allowlisted |
| sinatra_resolver 直连 | tax_info/user_groups_by_name/search_workspace_files/org_member_count/member_flyout_info | **安全**：全 403（internal-proxy 拦截） |
| AI 线程写 | delete/rename/duplicate/attachments/compressions 等 14 个 | **安全**：权限校验 403/404 |
| /api/user/state?fuid= | 绝对纯净 B + fuid=A/B | **安全**：fuid 声明身份也必须 ∈ cookie token 集合；返回数据全是 B 自己（之前"fuid=A 返回 A 数据"是多账号污染假象） |
| file_metadata 随机 uid | 重测记忆中的 fuid 越权模式 | **安全**：200 但 file_id/name/file_key/realtime_token/plan_id 全 null（该模式已修复/无泄露） |
| **ai_chat fuid 随机 uid（旧报告终极复测）** | 纯净B vs 原始B × fuid/header × 随机/A | **安全闭环，旧报告核心机制推翻**：fuid/header 声明身份必须∈cookie token 集合（纯净B+fuid=A→403，纯净B+header=A→401）；原始B 的 200 泄露是多账号 token 回退行为，攻击者 cookie 只有自己 token 时无法利用。原报告文件 H1-identity-claim-authz-bypass.md 已删除（假阳性） |

### 2026-08-19 报告处置
- **H1-identity-claim-authz-bypass(X-Figma-User-ID/fuid 注入)已由用户关闭，报告文件已删除**：2026-08-19 纯净 cookie 六组对照矩阵证明核心机制不成立(声明身份必须∈cookie token 集合,原 200 泄露是多账号 token 回退行为),详见 [经验学习15](../经验/全局经验/经验学习15.md)

## 2026-08-20 测试记录（livegraph mutation / AiMeter / Mcp 系列）

### 候选1: livegraph mutation 写操作 → 关闭（无 Full Dev Mode 写入基线）
- JS 逆向确认 mutation 写 = REST 写 + `lg_optimistic_mutation_uuid` + WS 乐观更新（WS 无 mutation 帧，messageType 枚举无 mutation 类型）
- 活跃写路径：`POST /api/files/related_links_batch`（body: link_batch[{node_id,file_key,link_name,link_url}]）
- 单文件端点 `POST /api/files/{fk}/related_links` 对 owner 也 403（疑似废弃）
- batch 矩阵：纯净 A 200 / 纯净 B 200 / 匿名 401；但 GET 读回 403 + WS DeveloperRelatedLinks 读回空 → **batch 对无权限写入静默丢弃**
- 根因：A/B 均 starter 计划 `canAccessFullDevModeV2: false`，related_links 功能不可用 → **写入基线不存在，越权无法验证**

### 候选2: AiMeterUsageView 跨文件 AI 用量 → 安全闭环
- args={fileKey}，查询 key [fileKey, 会话userId]（userId 硬编码 dZ("userId")）→ 永远返回自己的用量
- 纯净 B→A 文件：403 sinatraResolverError（内部路径泄露 `http://internal-proxy.prod.figma.com/api/internal/livegraph/sinatra_resolver/ai_meter_usage`，仅信息泄露）
- 纯净 A→B 文件：200 但返回 A 自己的用量（id 格式 `ai_meter_usage_team::{teamId}_{userId}_ai_credits_monthly`）
- 结论：数据硬绑定当前用户，fileKey 只决定 team metering bucket，无跨用户泄露

### 候选3: custom tools 401 根因 → 跳过（8-19 已闭环）

### 新攻击面: Mcp 系列 view → 全部安全/无面
| view | 定义要点 | 结论 |
|---|---|---|
| McpConnectorsView (H7) | args=[planId 可注入]，filter userId=dZ+planId，字段含 url/name | **公共 connector 目录**：B→A_PLAN 与 B→B_PLAN 返回完全相同的 19 个 public server（Amplitude/Asana/Atlassian/Box/...），planId 无过滤作用；mcpClientsV2 全空 |
| McpOauthClientsView (H8) | args=[]，filter userId=dZ 硬绑定 | tokenHash 非明文、clientSecretHash bannedFromViews、oauthApp/dynamicOauthClient 均有 checkCanRead，无注入面 |
| McpRemoteActivityView (H9) | args=[nodeIds,fileKey 可注入]，filter userId=dZ 硬绑定 | B 查 A 文件返回空；userId/nodeIds/fileKey 全部 bannedFromViews，安全 |
| DevModeMcpView (zd) | args=[fileKey]，file.canAccessDevModeMcp 带 dZ | 布尔权限查询，无面 |
| DevModeOptIn (zc) | args=[orgId]，org filter id=orgId+userId=dZ | 只能查自己 org 的 opt-in，低值 |

### 新发现: DeveloperLinks (zu) root 裸读通道 → 无法 POC，标记待验证
- root query `developerLinks`(args=[key])：filter 仅按 key，**无 checkCanRead / 无 dZ 绑定**，类型 DeveloperLink 为 **DangerouslyExempt**，字段 linkName/linkUrl
- view DeveloperLinks (zu) 直接暴露：subscribe args={key: fileKey}
- 测试：A/B/匿名 × A_design/B_FILE/community 文件（bv2nMIdFf4u3dESGail4sm=Dev Mode Test File）/qzDqStIDJyGbthpKiuvfwg → **全部 initial={}**
- A owner 视角 zm（DeveloperRelatedLinks/fileV2）也空 → **所有测试文件无 links 数据**；写需 `FileMustRequestUpgradeToEditDeveloperLinks`（付费），A 无 Dev Mode trial 资格（isEligibleForDevModeTrialV2: false）→ 无法造数据基线 → **越权无法实证**
- root `developerRelatedLinks`（args 版，无 checkCanRead）无 view 暴露 → 不可达

### 8-20 结论 & 遗留
- 8-20 三个候选全部裁决完毕：mutation 写关闭 / AiMeter 安全 / custom tools 跳过；Mcp 系列全部安全
- ⚠️ **事故：A_design 文件（5Gs4PaTz11Hlk2sqVnidBG）被改名成 t-99ff96**（验证编辑权限时 PUT /api/files/xxx rename），原名未恢复
- 遗留待办：
  - DeveloperLinks (zu) 越权读：需真实含 links 的私有文件验证（找 community 大厂付费文件或升级账号）
  - redeem 400 根因（需浏览器抓包真实桌面登录流程的 redeem 请求）
  - 企业 org 功能（SCIM/SSO/审计，需企业账号）；SVG 导入 XSS（需浏览器）
  - McpClient/McpServer mutation（createMcpServer 等 REST 端点未定位）
