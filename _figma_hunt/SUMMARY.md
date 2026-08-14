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
