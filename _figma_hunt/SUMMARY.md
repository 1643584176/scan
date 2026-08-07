# Figma H1 赏金测试 · 进度整理

更新日期：2026-08-07

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

1. 用新账号登录获取 session，对比登录态/匿名态 API 差异
2. livegraph preload 查询（FileBrowser*）是否可跨 teamId/orgId 越权
3. pagination_resolver 系列（org_*、admin_*、plan_ai_usage*）权限校验
4. Weave 域名（scope 新增）认证/越权面
