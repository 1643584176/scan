# Neon 攻击面分析(OpenAPI v2 离线,2026-09-03)

来源:neon.com/api_spec/release/v2.json(174 ops,120 paths)+ schema 细读。Server: `https://console.neon.tech/api/v2`(staging 同构:console-stage.neon.build)。

## 第一梯队(新功能 Beta 面 = 低撞车)

### 1. Data API(Beta,SubZero 内核)——最匹配技能,首攻
- POST/PATCH/GET/DELETE `/projects/{pid}/branches/{bid}/data-api/{db}`
- **SubZero 设置项即攻击面**:
  - `add_default_grants`: grant public schema 全表权限给 authenticated users —— 默认值?若默认 true = 权限放大
  - `jwt_role_claim_key` 默认 `".role"` —— JWT role claim 提取信任面
  - `db_anon_role` 默认 `"anonymous"` —— 匿名 role 配置
  - `db_extra_search_path` —— search_path 注入(extension schema?pg_catalog?)
  - `openapi_mode: ignore-privileges` —— 开放 API 文档忽略权限(信息面)
  - `db_max_rows`/`db_aggregates_enabled`/`server_cors_allowed_origins`/`skip_auth_schema`/`auth_provider`(neon_auth/external + jwks_url)
- 实测点:创建后拿 URL → REST over PG 方法集(select/insert/update/delete/rpc?)→ RLS 绕过、role claim 注入、方法变异(Netlify database-query 全套方法论迁移)、错误直透

### 2. Credentials(Beta)——S3 兼容凭据
- `createCredential`(scopes: `storage:read/write`, `ai_gateway:invoke`, `functions:invoke`;返回 `nak_live_<32hex>` + `nsk_live_<64hex>` Bearer+S3 secret,仅回一次)
- `revealCredential`(恢复 secret)、`rotateCredential`(保 token_id 换 secret)、`revokeCredential`
- GrantedScope 有 `telemetry:write`(用户不可申请——验证器 scope 检查面)
- 实测点:reveal 他人 token_id?scope 提权请求?credential 锚定 branch 的归属校验、交叉 branch 操作

### 3. Functions(Beta,nodejs24)——代码执行面
- `createProjectBranchFunctionDeployment` multipart zip 部署;`invocation_url` host = `<branch_id>-<slug>` Neon 托管域
- `registerProjectBranchCustomDomain`(entity_type: function;slug = entity_id)→ CNAME + LetsEncrypt(CAA 检查!);status 状态机 pending/ok(dns_status/binding_status)
- 实测点:slug 注入/冲突;custom domain 绑定他人 function?domain 校验绕过;函数运行时沙箱(env 泄露?)/构建链(zip 处理)
- 调用凭据:functions:invoke scope 凭据如何用?(JWT?签名?)

### 4. Buckets 分支对象存储(Beta)
- `access_level: private/public_read`;branchable(继承 ancestor 对象);`objects-by-prefix` 软删;`presign`(upload PUT/download GET,headers 必须原样);download 流式
- 实测点:**分支继承语义**(子分支删继承对象→父分支?);presign 作用域(他人 bucket?过期键?content-type 绑定绕过);public_read 匿名面;bucket 名跨分支唯一性

### 5. Auth 新版(Beta,Better Auth 内核)
- provider: mock/stack/better_auth;user directory 落 PG 表 `neon_auth.users_sync`
- `updateNeonAuthUserRole`(roles: user/admin + 自定义)——**admin role 提权?**(auth user → project owner?)
- `webhooks`(webhook_url 任意 → 后端回调 SSRF 面;enabled_events: user lifecycle/email OTP/org invite)
- redirect_uri whitelist(domain 级)→ redirect 校验粒度(domain 允许 → path 任意 = token 泄露面)

## 第二梯队(老面,撞车率高但可打状态机)

### 6. restore/finalize_restore 两步(快照恢复)
- restoreSnapshot → 新 branch(可 target_branch_id)+ finalizeRestoreBranch 替换原 branch(reassign computes)
- 两步窗口期权限态(类比 Netlify deploy 状态机:window 内对象状态混乱)

### 7. project/org transfer
- createProjectTransferRequest(ttl_seconds 用户可控)→ acceptProjectTransferRequest(org_id 可选)
- 个人→org 已 deprecated;org→org transfer(400 projects 上限)

### 8. roles/reset/reveal_password
- resetProjectBranchRolePassword / getProjectBranchRolePassword(412 条件?)——role_name 注入/特殊 role(如创建名为超管风格的 role)

### 9. snapshot/backup_schedule/logs
- createSnapshot(lsn/timestamp 参数!);backup_schedule PUT(paid);logs(LogQL escape hatch!)

## 首轮测试计划(staging 账号就绪后)
1. 建项目→分支→启用 Data API → 摸方法集/RLS/role claim/add_default_grants 默认
2. Bucket 面:分支继承 + presign + 交叉操作矩阵
3. Functions:部署 hello → invocation URL 结构 → env/沙箱侦察
4. Credentials:create → reveal → 用 scope 调用矩阵
5. Auth:redirect whitelist 校验粒度 + webhook URL

## 定级参照(奖励表)
跨租户/存储层/控制面 secret = Critical $5k;租户内提权 superuser/root/LFI = High $2k
