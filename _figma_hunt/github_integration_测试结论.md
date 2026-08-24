# Figma GitHub 集成子系统测试结论（2026-08-17）

## 背景
用户（A 账号 1643584176@qq.com）在 Make 编辑器 Settings → Integrations → GitHub 成功连接 GitHub。
目标：验证 B 账号（729488839@qq.com）能否越权操作 A 的 GitHub 集成。

## 关键事实

### 1. GitHub 连接 ≠ MCP 连接器
- livegraph `McpConnectorsView`（A 的 planId）确认：**A 连接 GitHub 后 mcpClients 仍为空**
- GitHub 集成走独立体系：`/api/integrations/github-app/*`（非 `/api/mcp/*`）
- MCP 连接器 UI 被 feature gate `mcp_plan_scoped_connectors` 禁用（starter plan 看不到）

### 2. GitHub 集成 API 端点全集（从 figma_app 889933 模块提取）
| 端点 | 方法 | 参数 |
|---|---|---|
| /api/integrations/github-app/setup | POST | plan_type, plan_parent_id, request_context, request_context_id, desktop_protocol |
| /api/integrations/github-app/installation/{id} | DELETE | 内部安装 UUID |
| /api/integrations/github-app/plans/{plan_type}/{plan_parent_id}/installation/admin | GET | plan 信息 |
| /api/integrations/github-app/user_access_token | GET | 需权限 |
| /api/integrations/github-app/org_user_repositories | GET | 需权限 |
| /api/integrations/github-app/repository_branches | GET | 需权限 |
| /api/integrations/github-app/create_pull_request | POST | body 参数 |
| /api/integrations/github-app/figma-make/{file_key}/remove_repository_mapping | POST | file_key |
| /api/integrations/github-app/install_authorize_redirection_url | GET | plan_type, plan_parent_id, request_source, request_origin_pathname |

### 3. 安装记录数据结构（A 基线 200）
```
installation: {
  id: "fabaef1b-6afd-40a7-a009-604ff5a80612" (内部 UUID)
  installation_id: "154303050" (GitHub 真实 id)
  login: "1643584176", account_type: "User"
  is_installed: true, is_active: true
  plan_type: "team", plan_id: "1666382706663462213"
}
```

### 4. B→A 越权测试矩阵（全部封死）
| 测试 | 结果 | 校验类型 |
|---|---|---|
| B DEL A 安装 (内部 UUID) | **403** | 安装归属校验 |
| B DEL A 安装 (GitHub id) | **400 not found** | UUID 查找 |
| B remove_map (A 私有 fileKey) | **403** "don't have permission to edit this file" | 文件编辑权限 |
| B remove_map (A 公开 fileKey) | **403** 同上 | 文件编辑权限（公开也不行） |
| B repos / token (任何 fileKey) | **403** | 权限校验 |
| B 生成 A plan 授权 URL | **403** | plan 权限校验 |
| A setup 重放 | **409** "Plan has already been connected" | 幂等保护 |

## 结论
**GitHub 集成权限模型完整，无 B→A 越权路径**。三道校验：
1. 安装归属校验（安装管理 API）
2. 文件编辑权限校验（文件级操作 API，公开文件不豁免）
3. plan 权限校验（授权 URL 生成）

## 可迁移方法论
1. **功能归属判定**：连接成功但抓不到请求时，用 livegraph view 直接查服务端状态（McpConnectorsView 的 mcpClients 为空 = 证明连接不落 MCP 表）——服务端数据是功能归属的确定性证据
2. **400 route typechecking 错误泄露必需字段**：`install_authorize_redirection_url` 报 "Required field 'request_source' is missing" → 这是确定性参数来源，迭代补齐
3. **两套权限模型对照**：MCP（plan gate + owner 校验）vs GitHub 集成（归属 + 文件权限 + plan）——Figma 新集成系统的权限设计一致性强

## 5. livegraph 通道验证（2026-08-17 补充）
### 5.1 githubAppStatus 前端实现 = livegraph view（非 REST）
- 静态追踪链：2471/63053 (`u=n(81772)`) → figma_app 81772 (导出 `o`=githubAppStatus hook) → `(0,i.$3h)({planId,planType})` → 864950 模块 `o("GithubStatusView",["planId","planType"],"edd3087897...")` —— **livegraph view 注册**
- view 内部经 sinatra resolver：`/api/internal/livegraph/sinatra_resolver/github_app_status` + `github_user_status`（错误帧泄露内部服务 `internal-proxy.prod.figma.com`）

### 5.2 WS URL userId 参数契约（关键）
- **userId 空 → resolver 401 无 reason**（连 A 自己都拿不到）
- **userId=会话用户 uid → resolver 正常返回**：appStatus/installationId/githubOrgId/githubUserName/githubUserAvatarUrl/userAccountAuthorized
- 参数格式：planId=bigint 字符串（team id），planType="team"；planRecord uuid 被拒（"expected string representation of bigint"）

### 5.3 B→A 越权矩阵（livegraph 层，封死）
| 会话 | userId | 结果 |
|---|---|---|
| A | A_UID | ✅ 完整数据（appStatus=installed, githubUserId=247122667） |
| B | B_UID | **403** "You don't seem to have permission to do that."（plan 权限校验） |
| B | A_UID（冒充） | **401**，query key 从 [A_UID,..] 剥成 [null,..]（会话一致性校验） |
| B | 空 | 401（无用户上下文拒绝） |

**结论：livegraph 通道与 REST 权限模型一致（会话一致性 + plan 权限），无 B→A 越权路径。**

### 5.4 附带发现（低危，不报告）
1. 错误帧泄露内部 resolver 端点 + internal-proxy.prod.figma.com 服务名（Informational）
2. A 的 GitHub 信息（githubUserId=247122667 / 用户名 1643584176）为 GitHub 公开数据

### 5.5 方法论沉淀
1. **REST 不可达 → livegraph view 通道**：githubAppStatus 无 REST 端点，view 注册表（`o("ViewName",[args],hash)` 模式）是确定性来源，figma_app 864950 是 view 注册库
2. **WS URL userId 是 resolver 查询参数**：空 userId=401 无 reason（服务端无用户上下文），填会话 uid 才可达——错误码语义（401 无 reason vs 403 有消息）可区分"无上下文"与"权限拒绝"
3. **会话一致性校验特征**：伪造 userId 时 query key 被剥回 [null,...]——服务端显式清除不一致参数，这是强校验指纹
