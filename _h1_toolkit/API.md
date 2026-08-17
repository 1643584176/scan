# H1 GraphQL/REST API 确定性调用知识

> 全部内容来自 2026-08 实测探测（`_h1_platform/round*.log`），**已验证可用**。
> 使用原则：直接按本文档调用，禁止重新探测；新增需求先查本文档再决定是否探测。

## 1. 基础信息

| 项 | 值 |
|---|---|
| GraphQL 端点 | `POST https://hackerone.com/graphql` |
| Content-Type | `application/json` |
| 认证 | 普通查询（teams/reports/search 等）**无需 cookie**，匿名可调 |
| introspection `__schema` | **被禁**（`Field '__schema' doesn't exist on type 'Query'`） |
| introspection `__type` | **可用**（探测字段类型/枚举时用） |
| CSRF 保护 | 仅 introspection 类请求需要 `X-CSRF-Token` 头 + `__Host-session` cookie；普通查询不需要 |
| 请求头 | `User-Agent` + `Origin: https://hackerone.com` + `Referer: https://hackerone.com/hacktivity/overview` |

## 2. Query 根字段（39 个，已确认）

```
me  reports  team  report  organizations  teams  node  organization  features
search  pentest  users  weaknesses  opportunities_search  organization_inboxes
report_retests  report_intent  maintenance_banner  cve_entry  ranked_cve_entries
user  cwe_entry  resource  hai_plays  analytics  document  severity_calculator
report_retest_user  conversation
```

## 3. hacktivity 列表抓取（核心用法）

```graphql
query HacktivitySearch($query_string: String, $first: Int, $after: String, $sort: SortInput) {
  search(index: CompleteHacktivityReportIndex, query_string: $query_string,
         first: $first, after: $after, sort: $sort) {
    total_count
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on HacktivityDocument {
        id
        report { title }
        team { handle name }
        reporter { username }
        severity_rating total_awarded_amount disclosed_at submitted_at cwe
      }
    }
  }
}
```

variables:
```json
{
  "query_string": "disclosed:true",   // 或 "disclosed:false"
  "first": 50,                          // 每页最多 50
  "after": null,                        // 第一页不传；后续传上一页的 endCursor
  "sort": {"field": "latest_disclosable_activity_at", "direction": "DESC"}
}
```

返回字段：`id`(global_id)、`report.title`、`team.handle/name`、`reporter.username`、`severity_rating`、`total_awarded_amount`(赏金)、`disclosed_at`、`submitted_at`、`cwe`。

**分页机制（关键，易踩坑）**：
- `hasNextPage` **恒为 false**（后端 bug/特性），不能用作循环条件
- `endCursor` 是 **base64 编码的 offset**（如 `"NTA"` = base64("50")，下一页从 51 开始）
- 正确循环：取本次 `endCursor` 作为下次 `after`，以“本次返回节点数 < first”作为结束条件
- 完成脚本：`scripts/hacktivity_fetch.py`（已封装以上逻辑）
- **total_count=10000（上限）**，实际披露报告约数千条

## 4. search 索引（IndexEnum! 有效值，已探测）

| 索引名 | 状态 | 说明 |
|---|---|---|
| `CompleteHacktivityReportIndex` | ✅ 可用 | hacktivity 主索引（上文用法） |
| `OpportunitiesIndex` | ✅ 可用 | 项目机会搜索（program 列表） |
| `DuplicateDetectorReportsIndex` | ✅ 返回 0 | 空 |
| `NotificationsIndex` | ✅ 返回 0 | 空 |
| BookmarkTeamIndex / CredentialsIndex / ProgramAuditLogIndex / UpdateLlmMessageIndex / messageIndex 等 | ❌ 无效 | `Argument 'index' has an invalid value` |

无效索引会直接报错泄露枚举值不存在；`__type(name:"IndexEnum")` 可枚举全部有效值。

## 5. opportunities_search（program 列表，匿名可用）

```graphql
query {
  opportunities_search {
    nodes { id name handle state submission_state }
  }
}
```

- 返回 H1 自营项目：`security`(HackerOne)、`phabricator`，`state: public_mode`，`submission_state: open`
- 过滤器 `filter: {terms: {submission_state: ["open"]}}` 有效；枚举值 **open/paused/disabled**（closed 无效）
- `bool.must/must_not` 结构受限：`term` 内字段名需为 Int 类型（如 id），`term.state` 字符串会报 coercion 错误——**过滤功能有限，直接用 queryString 更可靠**

## 6. 报告详情 REST 端点（重要）

```
GET https://hackerone.com/reports/{id}      # 公开报告：匿名 200，完整 JSON
GET https://hackerone.com/reports/{id}.pdf  # 需 cookie；匿名 404，有效 ID 500
```

`/reports/{id}` 返回完整报告详情：标题、描述（vulnerability_information 全文）、reporter、team、state/substate、severity_rating、cve_ids、disclosed_at、can_view_report 等。**公开披露的报告匿名可读全文**。

## 7. CSRF/session 获取（如需带认证调用）

```
GET  https://hackerone.com/user/csrf
→ 返回 {"csrf-token": "..."} 并 Set-Cookie: h1_device_id + __Host-session
→ 后续 introspection 请求带 X-CSRF-Token: <csrf-token> 头
```

## 8. 其他已知可用查询

- `teams { nodes { id handle } }` — 匿名可用，按 handle 查团队
- `resource(url: "...")` — LayoutDispatcher，解析任意 URL 资源类型（Team/User），返回 id/handle/url
- `cve_entry(cve_id: "CVE-2021-44228")` — CVE 详情（描述/EPSS/影响产品）
- `ranked_cve_entries(first:10, search:...)` — CVE 排行（含 `pageInfo.hasNextPage` 分页）
- `weaknesses { nodes { id _id name external_id } }` — CWE 列表
- `users` — 按 email/phone/username 过滤查询**已废弃**（返回语法错误），不可用
- `pentest(id:1)`、`report_retest_user(id:1)`、`report_intent(id:1)` — 均返回 null（无数据）

## 9. 已知限制（避免重复尝试）

- ❌ `__schema` introspection 被禁（返回 undefinedField 错误）；用 `__type` 逐字段探测
- ❌ Hasura 风格 header 注入（x-hasura-admin-secret / role / X-Admin）无效
- ❌ 旧 JSON 端点 `hacktivity/overview.json` 已废弃
- ⚠️ WebFetch 抓 hacktivity 页面拿不到数据（JS 渲染），必须走 GraphQL
