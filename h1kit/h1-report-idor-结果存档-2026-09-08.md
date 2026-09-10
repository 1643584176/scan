# H1 平台越权读报告 IDOR 测试结果存档(2026-09-08)

## 目标与假设
- Scope: https://hackerone.com/ 全站(H1 平台自身,非子项目)
- 假设:已知他人私有报告 id(邮件 duplicate 通知编号),以普通 hacker 身份越权读取(只读)
- 测试身份:xxbo(用户主 hacker 账号,Neon hunter)

## 测试样本
| id | 归属 | 匿名 | 登录直查 | 说明 |
|---|---|---|---|---|
| 3732660 | Neon(他人原报告,私有,未披露) | EMPTY | EMPTY | 权限正常 |
| 242816 | 老报告(未知归属) | EMPTY | EMPTY | 权限正常 |
| 3992341 | Neon(本人报告,duplicate) | EMPTY | VISIBLE | 基线(自己可见) |
| 2487889 | H1 平台自身已披露(2024 bugs.json IDOR) | VISIBLE | - | 公开对照 |

## 测试路径与结果(全部登录态 xxbo)
1. `reports(where:{id:{_eq:N}}){nodes{...}}` — 3732660/242816 空;3992341 返回 ✓ 行过滤正常
2. `reports(database_id: N)`(ReportPage 参数风格)— 3732660 空;3992341 返回 ✓ 同权限模型
3. `reports(where:{team:{handle:{_eq:"neon_bbp"}}})` program 列表 — 只返回自己参与的 2 条(4000158/3992341),无他人私有报告混入 ✓
4. `reports(where:{_and:[{team...},{id...}]})` 组合 — 3732660 空 ✓
5. **`duplicate_information` 关联(3992341 → 3732660)** — ⚠️ 返回原报告元数据:title/severity_rating(high)/severity_score/submitted_at/substate(triaged)
   - **终判:功能设计** — UI(report 页 duplicate 卡片)同步完整显示 title/severity/时间/asset/weakness/CVE,与 API 一致;H1 故意给被 dup reporter 看原报告元数据,不给正文/评论/附件
   - `ReportDuplicateInformation` 为受控精简类型:state/reporter/team/vulnerability_information/activities 均 undefinedField(字段级控制生效)

## 结论
- **IDOR 越权读他人私有报告:证伪(不可复现)**
- H1 GraphQL 报告访问权限模型完整:行级过滤(匿名=仅披露;登录=reporter/participant/team member)+ 字段级类型控制
- duplicate 元数据卡片(标题/严重度/时间)为平台设计功能,非漏洞

## 今日新增通道(2026-09-08 续,全部登录态 xxbo + 匿名对照)
| # | 通道 | 结果 |
|---|---|---|
| 1 | search 5 索引(DuplicateDetector/CompleteHacktivity/Opportunities/Notifications/StoredQueries) | 全角色/披露过滤;DuplicateDetector 对 hacker 恒空(连自己报告都搜不到);CompleteHacktivity 只含 public:true |
| 2 | activity(id:) 直查(全局自增序列校准:2024-05=2729万/2026-05=4426万,~2.3万/天) | 相邻 id 必属别人 → 5 连 NOT_FOUND = 统一遮蔽 |
| 3 | 自己报告活动链嵌套:ActivitiesBugDuplicate.original_report { title vulnerability_information } | **null**(关联对象层同过滤) |
| 4 | report(id:){team{reports/team_members/reporters}} 嵌套 | 非 member 全 0(比 root 更严) |
| 5 | triage_inbox_items(补 view 枚举 pristine/owned_by_me/prioritization 后) | 0 条(此前 500 = 缺参非权限) |
| 6 | gateway_users / report_retests(177) / OpportunitiesIndex | 0 / 公开复测市场(全 resolved) / 公开 program 数据 |
| 7 | report_intent / machine_learning_inference_result / recon_context(id Int 直查) | null/不存在(独立 id 序列不可枚举) |
| 8 | ReportIntent 类型 introspection | 含 vulnerability_information/report/title = AI 分析对象;id≠report id |
| 9 | available_chart_definitions / analytics_reports / analytics_chart | 空/0(team 上下文隔离) |
| 10 | user(username:) 节点(User 190 字段) | reports 只含已披露;activities 别人=0;notifications=[];email/balance/calendar_token/drafts 全 null/0;email_alias=username@wearehackerone.com(公开派生) |
| 11 | deprecated 字段面(includeDeprecated:true) | Query 仅 report/session/user/Report.undismissed_triage_inbox_items 4 个,全测 |
| 12 | /bugs.json 参数旁路(数组/重复/null/空格/无 text_query) | 全闭;200=org 有效(非 member 空)/404=org 无效(oracle 但无内容) |
| 13 | 附件面:公开报告 .json attachments { id 整型, expiring_url=S3 presigned(随机 key+1h 签名) } | /attachments/{id} 等 REST 全 404;S3 key 随机不可枚举 |
| 14 | REST .json 家族 | bugs.json/notifications.json 活(401/406);reports.json/programs.json/users.json 等 404;hacktivity/opportunities.json 301 |
| 15 | introspection __type(includeDeprecated) | __schema 禁但 __type 全开放 = schema 可完整重建(高复用资产) |

## 最终结论(2026-09-08 全面测试后)
- **H1 平台(2026-09)私有报告读取权限模型:行级过滤 + NOT_FOUND/null 统一遮蔽 + 字段级受控类型(duplicate_information) + 索引角色/披露过滤 + 关联对象层过滤 + deprecated 老字段同过滤**
- 30+ 通道(本会话 20+ 新增)全闭,无越权读他人私有报告的路径;2024 bugs.json IDOR 修复完整(org 过滤全局生效)
- 剩余理论面:写入类(mutation,违反零破坏纪律)/跨账号(无第二账号)/UI 层(已对照)

## SQL 注入专项(2026-09-08 续,h1x49 系列,匿名只读)
| 面 | 测试 | 结果 |
|---|---|---|
| 1 | reports where 谓词(_like/_ilike/_similar/id_like/_or 内引号闭合/OR 1=1/AND 1=1) | 全 0/字面匹配,无报错无布尔差异 = 参数化;%'% 偶发超时复测 2 次均 200(475 条,含撇号标题数,一致) |
| 2 | 单值参数 team(handle)/organization(handle)/user(username)/external_program(handle)/cve_entry/cwe_entry | 全统一 NOT_FOUND/null,payload 与垃圾值行为一致 = 精确匹配参数化 |
| 3 | reports handle/state/substate/assignee | state/substate 枚举类型、assignee 输入类型 = GraphQL 解析层拒绝;handle 任意值=0(空串=12488 全可见,过滤正常) |
| 4 | resource(url:) | URI 格式校验 PARSE_ERROR,无拼接 |
| 5 | Hasura 直连 /v1/graphql 等 8 路径 | 全 404 |
| 6 | search query_string(Lucene 语法面) | **字段白名单 8 个**(title/content/team/reporter/cwe/substate/severity_rating/disclosed_at),其余报 "not searchable";Lucene 语法全活跃(fuzzy/OR/NOT/通配/范围);reporter:xxbo=0(私有报告不入索引);索引=公开 hacktivity(披露报告+程序公开活动条目);无私有数据触达 |
| 7 | disclosed_at:2024* 通配符 | **稳定 500 ×4**(date 字段 trailing wildcard 透传 ES 内部异常);范围/大于语法正常 = 仅 DoS 面,不深入 |

**SQLi 结论:全闭** — where 谓词参数化、单值参数精确匹配、类型化参数解析层拒绝、ES 查询字段白名单且仅公开数据。无注入可利用点。

## /bugs inbox 前端考古(2026-09-08 续,h1x50 系列,bundle _h1x4_app.js)
- **数据端点实锤**:Backbone VX collection `url(e)=`/bugs${e?`.json`:``}?${inboxState.toParam()}``,fetch `{method:'POST'}` → **POST /bugs.json?<完整查询串>**(XHR+CSRF);响应 JSON={bugs:[],pages,count,...},parse 把多余顶层属性 set 回 inboxState
- **用户 inbox URL 查询串参数 = POST /bugs.json 参数全集**:subject/report_id/view/substates[]/reported_to_team/text_query/program_states[]/sort_type/sort_direction/limit/page
- **subject 语义**:`user`=自己的报告;`<team handle>`=该团队 inbox(subject 切换器数据来自 **GET /inbox/subjects?handle=**,handle=subject 值);前端 isValidSubject(subject=user 或 apollo me.teams)只做 UI fallback,直接 fetch 可绕过
- **params 全集**:[subject,team_id,report_id,view]+viewParams[filters,substates,severities,weaknesses,assets,hackathons,assigned_to_user_ids,assigned_to_group_ids,reporter_usernames,reporter_ids,**report_ids**,custom_inbox_ids,reported_to_team,text_query,available_filters,program_states,custom_fields,start_date,end_date]+pagination[sort_type,sort_direction,limit,page]
- **_id 结尾参数**(report_id/team_id)initialize 时 parseInt(数字清洗);program_states 枚举 2=sandboxed/3=da_mode/4=soft_launched/5=public_mode(ProgramStateFilter 仅 subject=user)
- bugs.json 另一调用:duplicate typeahead POST body{text_query,organization_id,persist:false,view:custom,...}(=2024 PoC 参数,body 表单);organization inbox 用 GET bugs.json?organization_inbox_handle=
- **待测面(需登录态)**:subject=他人 team handle(neon_bbp/security)越权列表;report_id/report_ids[] 单/多报告直查他人私有 id;team_id 注入;reported_to_team 填值;删 subject 服务端默认

## /bugs inbox 变异测试结果(2026-09-08 续,登录态 xxbo 执行)
| 变体 | 结果 | 判读 |
|---|---|---|
| A0-A4 subject=user/neon_bbp/security/github/删 | 全部 200,恒返回自己 3 条 open 报告 | **subject 服务端强制绑定当前用户**,team handle 被忽略(宽容处理,非 403 而是返回自己的 inbox) |
| B1 report_id=3732660 | 200 恒返回自己列表 | report_id 在 POST bugs.json 被忽略(详情走其它通道,已闭) |
| B2/B3 report_ids[]=3732660/2487889 | 400 error(私有/公开一致) | 解析层拒绝,非权限差异 |
| C1 team_id=13 | 200 恒返回自己列表 | team_id 被忽略 |
| C2 reported_to_team=13 | 200 count=0 | **唯一生效的过滤参数**;语义=自己的报告按 team 子集过滤(收缩集合,无越权) |
- 响应 extra_keys=count_capped(总数封顶保护);open 视图 count=3(6 条报告中 3 条非 open 被 substates 过滤,过滤正常)
- **结论:/bugs.json?<inbox 全参数> 面闭合**——后端模式:未知 subject/team_id/report_id 一律忽略并返回当前用户 inbox(安全失败),reported_to_team 仅在自己报告集合内收缩过滤
- **GET /inbox/subjects?handle= 测试(登录态 xxbo)**:handle=user/neon_bbp/security/github/空 全部 200 且响应完全一致 = 恒返回当前用户 subjects({"teams":[],"user":{"name":"xxbo","views":[open/needs_more_information/pending_bounty...]}});**handle 参数被忽略**,teams=[] 确认 xxbo 非任何 team member;无团队视图配置泄露 → 面闭合
- **inbox 方向终局闭合**:subject/handle/team_id/report_id 参数全忽略(宽容降级到自己的数据),reported_to_team 仅收缩过滤;view 键由服务端命名视图决定(open/needs_more_information/pending_bounty 等)

## dup/original 链深测(2026-09-08 续,h1x52k-v 系列,登录态 xxbo)

**背景确认**:用户 3992341(Neon pg_repack 提权)被 dup 到 **3732660**(目标私有报告,high/triaged/2026-05-13);3978448→3951926(Vercel);4006058→3932185(Figma)。用户的"只有标题"来源 = duplicate_information(设计行为)。

### 测试矩阵
| 通道 | 结果 | 判读 |
|---|---|---|
| report(3992341).original_report / original_report_id | original_report_id="3732660" 返回;original_report=**null** | 顶层对象遮蔽,只给 id |
| report(3732660) 直查 | NOT_FOUND | 私有遮蔽 |
| activities 连接:ActivitiesBugDuplicate.original_report | **null**(3 条 dup 报告一致) | 活动层独立 resolver 也遮蔽;message=完整 dup 关闭消息(无 original 内容) |
| duplicate_information | {_id:3732660, title:"Compute environment RCE from pg_repack rule context that lets tenant open cloud_admin dblink session and execute COPY PROGRAM", substate:triaged, severity_rating:high, submitted_at} | **标题级信息设计可见**;ReportDuplicateInformation 类型仅 7 字段(id/_id/title/substate/severity_rating/severity_score/submitted_at),**无正文通道** |
| deduplication_action_recommendation | null | HAI team 工具,reporter 不可见 |
| deduplication_recommendations | [] | 同上 |
| dupe_window | null | reporter 无申诉窗口对象 |
| NotificationsIndex 全量 10 条 | report_id 全为自己的报告;类型仅 CommentPosted/BugClosed | 通知索引按接收者隔离 |
| notification.report.vulnerability_information | 全部返回**自己的报告**正文(3992341 完整 PoC 也在) | 权限正确,非越权 |
| activity(id) 邻居 ±0/±1/±10/+1000 | 自己的 9 个 activity_id 返回 typename;所有邻居 NOT_FOUND | 无法区分空洞/遮蔽(无他人私有活动 id 来源) |
| resource(url: /reports/3732660) | NOT_FOUND | URL 解析器走标准权限;公开 2487889 → Report 正常 |

**bundle 考古发现**:
- 前端 duplicate_information fragment 选 {id _id severity_rating severity_score submitted_at substate title}(标题级=UI dup 横幅)
- DeduplicationActionRecommendation.original_report 前端只选 {id _id title substate submitted_at}
- duplicate typeahead(POST /bugs.json text_query+organization_id+duplicates_must_have_no_ref)是 **team 端标记 dup** 搜索,需 team 上下文

### report_intent 面(HAI 提交向导草稿)IDOR 测试
- **数据流**:SubmitWithHaiButton mutation resumeOrCreateReportIntent(team_id) → databaseId → URL /hai/report_assistant/<id>;页面查询 ReportIntentV2Query(id: Int!);me.report_intents(first:100, version:1) 列自己的
- **ReportIntent 类型**:id/_id(Int!)/title/description/impact/state/metadata/attachments/report(Report)/team/conversation/**vulnerability_information**/custom_fields
- **xxbo 无历史 intent**(6 条报告均普通表单提交);创建 2 个空草稿做锚点:312073(neon)/312075(figma);Vercel team 创建失败(未启用 report_assistant)
- **id 序列**:312073↔312075 间隔 1-2 秒含 312074(他人窗口,存在概率 94%);intent 总量 ~31 万
- **枚举结果**:312074 null;312076..312130(55 个,≈23 分钟窗口)全 null;±50(D 组)全 null;匿名全 null;**命中仅自己的 2 个**
- **判读**:新建 1-2 秒的他人 intent 不可能已提交删除仍 null → **owner 校验遮蔽(null 而非 NOT_FOUND)**,无 IDOR → 面闭合
- 副作用:账号残留 2 个空草稿(312075/312094,312073 已删 312094 重建;可在 /hai/report_assistant 丢弃,无内容)
- GraphQL 限制:同字段 alias 上限 3 个/selection set(批量枚举需每 3 个一批或串行)

**dup/original/intent 链终局**:所有 Report 对象引用路径(original_report 顶层/活动层/HAI 工具/通知 report/intent report)一律按访问者权限遮蔽或 null;唯一可见的他人报告信息 = duplicate_information 标题级(设计);通知/活动/附件均自己的。3732660 目标在现有通道下仅元数据(标题/严重性/时间/状态)可达。

## conversation 面深测(h1x53 系列,2026-09-08 续,登录态 xxbo)

**入口发现**:conversation(id: ID!) 根查询 → ConversationUnion(6 类型:AtlassianAgent/Exploit/Linear/Remediation/ReportAssistant/Validation agent conversation);Report 挂 5 种 agent 会话字段(hacker 视角值级 null 遮蔽);ReportIntent.conversation → ReportAssistantConversation(自己可读)

| 事实 | 数据 |
|---|---|
| 会话 gid 形态 | gid://hackerone/Conversations::Views::ReportAssistantConversation/<自增 id>;id 数字需 base64 gid 格式(裸数字 → NOT_FOUND,已证) |
| 序列语义 | 973082→973154 一小时 Δ=72(共享序列,triage agent 会话占多数;intent 同期仅 Δ19 → 非 1:1) |
| 自己会话可读 | 973069(C1b,07:34 创建,1.5h 后仍可读,无 TTL)、973082(H0a 单查完整含 entries) |
| entries 结构 | ConversationEntries::Message(data.message=正文)/ToolCall;actor=hackbot;双层 inline fragment 必需 |
| **H2 终判** | 973123..973153(31 位置 × 6 类型 = 186 单字段请求)全显式 NOT_FOUND errors,0 静默 null;按 Δ=72/h 占位率该窗口应有 ~20+ 真实会话 |
| 删除正控 | 973069 随 intent 312073 删除 → NOT_FOUND(删除机制存在但无法解释全局 ~1/min 删除速率) |

**关键方法论教训**:3-alias 同字段批量查询,批次内含"存在可读"id 时整批被**静默 null 化(无 errors)**(G0 证);全 miss 批次正常返回 errors。→ 邻域枚举一律单字段/2-alias,且必须区分 errors 与静默 null

**结论:conversation(id:) 参与者级鉴权** — 他人会话(含 triage agent 会话,6 类型全覆盖)统一 NOT_FOUND;与 report_intent(owner 校验 null 化)/Report(行过滤)同族防护。IDOR 不可行 → 面闭合

## team 私密配置面(J 组,2026-09-08,登录态 xxbo)
| 通道 | 结果 | 判读 |
|---|---|---|
| external_integration_credentials(team_id: security/13 + neon/92627 × provider linear/atlassian) | 全 null | 成员校验,非 member 不可见(api_key/email 字段存在但拿不到) |
| automation(id: 1..12 × org_handle security/hackerone) | 24 全 SILENT_NULL(无 errors) | org 校验 null 化;org_handle 猜测或成员校验其一未过 |
| derived_pentest(origin_id: 3732660/3992341 × 5 origin_type) | 全 null | 无派生或权限过滤 |
| hai_chat / hai_task(id: gid 1..3) | 全 null | 不存在或不可见 |

**结论:team 侧私密配置对象(凭据/自动化)对普通 hacker 值级 null 化,与其它面同族防护,无 IDOR**

## REST 详情 JSON 面(M/N/O/P 组,2026-09-08 续,登录态 xxbo)

**端点确认**:`/reports/{id}.json`(及 `/reports/{id}?format=json`)为内容级端点——响应含 vulnerability_information(完整正文)/reporter/team/severity/weakness/attachments/voters/summaries/original_report_id+url/abilities 等全字段(自己 200 验证 5251 字符正文);**攻击价值 = 拿到即读全文**

| 变体 | 结果 | 判读 |
|---|---|---|
| 3732660(.json/format=json/变体矩阵 20+) | 恒 404 text/plain 空 | 控制器级权限 404(路由活);404 HTML=路由死(子路径/重复段/OPTIONS) |
| 3992341/2487889(自己/公开) | 200 全字段 | 行级过滤与 GraphQL 一致 |
| query 覆盖(own_path+tgt_query / tgt_path+own_query) | 恒返回路径 id | 路径优先,无参数覆盖 |
| HEAD/JSONP/ids[]/大写/前导零/编码点 | 同 404 | 无方法/格式绕过 |
| /reports/export?id= 系列(GET/POST/ids[]/team_id/路径) | 400 "id must be an integer" 恒 | 参数形态不明或另一对象,弃 |
| /bugs/reported_to_teams | 200 = 恰好自己报过的 3 team(figma/neon_bbp/vercel_sandbox) | 按当前用户过滤,非平台级 |
| Backbone 子路径(external_users/invitations/collaborators/summaries/mediation) | 404 HTML(自己/他人/公开一致) | 路由已死 |
| /hai/agentic_ui_mcp/resources/read | 仅 ui://prefab/app 200(前端硬编码);其余全 403 "Resource not permitted" | 固定白名单,无 oracle |

**结论:REST 详情面 = GraphQL 同权限模型**(行级过滤 + 控制器级 404),无绕过 → 面闭合

## 关联路径全量扫描(Q/R 组,2026-09-08,登录态 xxbo)——Report 199 字段 + Activity 类型全集

**方法**:对全部 6 条自己报告逐字段测 Report 类型 199 字段中所有关联/内容类字段 + introspection 全部活动类型成员

| 字段/类型 | 结果 |
|---|---|
| cloned_from/clones/duplicates/reference/reference_link/source | 全 null/空(自己报告无 clone 关系) |
| report_metadata | 非 null 但空壳(仅 id/_id) |
| hai_report_data/extracted_report_data/report_generated_content/report_assistant_submission_summary | 全 null(reporter 侧不可用) |
| i_can_clone/i_can_view_duplicate_suggestions | null(仅 team 上下文) |
| ActivitiesBugDuplicate.original_report_id | **标量可见**——3992341→3732660;4006058→3932185;3978448→3951926(活动层直接拿原报告 id) |
| ActivitiesBugDuplicate.original_report 对象 | null(对象层遮蔽,与 Report.original_report 一致) |
| ActivitiesBugCloned/ExternalUserJoined/ReferenceIdAdded 活动 | 自己 6 条报告均不存在 |
| deduplication_recommendations/action | 空(team dedup 建议对象对自己不可见) |
| ActivityUnion 语法 | union 上不能直选字段,须 __typename + inline fragment |
| __schema 全量 introspection | 禁用(0 types;仅 __type 单类型可用) |

**结论**:关联路径面(用户偏好的 ActivitiesBugDuplicate resolver 探测法)确认遮蔽为**对象级统一**——同类型上 id 标量放行、对象遮蔽、内容字段空,权限实现在 Report 加载层(load_report 按参与者过滤),非字段遗漏。3732660 可达信息 = id + duplicate_information 7 字段(设计功能)。关联面闭合。

## SQLi 面全维度补测(S/T/U/V/W 组,2026-09-08 续,登录态 xxbo)——DB 特征语法矩阵

**背景**:h1x49(匿名)已闭 where 谓词/单值参数/枚举/ES 白名单;本次按用户要求补 DB 特征语法(MySQL/PG 函数/变量/关键字/注释/堆叠/子查询/布尔)+ 登录态端点

| 面 | 测试 | 结果 |
|---|---|---|
| GraphQL where 值 | title _eq 带 SLEEP(3)/pg_sleep(3)/extractvalue+version()/@@version+`#`/`' OR '1'='1`;team handle 特征值 | 全 200 与基线同 0 结果,无延迟/报错/布尔差异 = 参数化 |
| conversation(id:) 特征值 | gid+`' OR '1'='1` | selectionMismatch(union 语法先拒,poll未达 resolver) |
| **bugs.json 后端识别** | sort_type 枚举错误消息泄漏白名单 | **含 pg_search_rank = Rails pg_search gem(pg 全文搜索,非 ES!)** |
| bugs.json sort_type/sort_direction/limit | 注入特征 | 全 400 枚举白名单(created_at/latest_activity/.../pg_search_rank;ascending/descending;10/25/100/1000)——校验器先拒 |
| bugs.json text_query(tsquery 面) | `&`/`|`/`!` 布尔语法 | 语法活跃(结果集按布尔变化)但仅作用于 tsvector;`x' OR SLEEP(3)-- -` 无延迟 |
| 悬空 tsquery(`bug &`/`(bug`) | 200 降级返回全部 | **解析异常被捕获降级(count=3=无过滤),无 500 无错误泄漏** |
| reported_to_team 特征值 | `13 OR 1=1`/`13'` | count=0(整数解析失败收缩),无注入 |
| /reports/export?id 特征 | `1'`/OR/子查询/堆叠/0x1 | 恒 400 "must be an integer"(严格整数解析,消息无变化) |
| /inbox/subjects?handle 特征 | handle=特征值 | 忽略(恒返回自己 subjects) |

**结论:SQLi 全维度闭合** — GraphQL 参数化 + REST 枚举白名单校验器 + pg_search tsquery 异常降级(无泄漏)+ 整数严格解析;MySQL/PG 函数、变量、关键字、注释、堆叠、子查询、布尔语法全部无注入信号(无 500/无延迟/无布尔差异/无结果集异常)

## 根字段全清单补测(X/Y/Z 组,2026-09-08 续,登录态)——114 字段对照扫荡

**方法**:__type(name:"Query") 全字段+args 拉取(114 个)对照历史已测清单 → 找出 10 个从未测字段逐一深测

| 字段 | 结果 | 判读 |
|---|---|---|
| node(id:) Relay loader(Report 3732660/3992341/2487889 gid) | 他人 NOT_FOUND "Report does not exist"/自己公开正常 | 与 report(id:) 同权限,无旁路 |
| node(Conversation gid 973069) | NOT_FOUND(loader 不支持 Conversation 类型,非信号) | 类型白名单差异 |
| node(User/Team/Activity gid) | 正常;Team 13 __typename=Engagements::BugBountyProgram | loader 部分类型可用 |
| webhook(id: 1/2/13) | 全 null(值级无 errors) | team 校验 null 化 |
| triage_inbox_items(report_id: 3732660/3992341/1/2487889/默认) | **全 500 STANDARD_ERROR** | 非 member 调 team triage 工具恒 500(policy 抛错,无 oracle 无内容) |
| completed_recommendations(team_ids: [13]/[92627]/[99999999]) | 全 500;无参=missingRequiredArguments | 同上,非 member 恒 500 |
| intake_workflow(report_id: 3732660) | null | 闭合 |
| assignable_teams(report_ids: [3732660]) | nodes [] | 闭合 |
| machine_learning_inference_result(id: 1)/recon_context(id: 1) | NOT_FOUND | 闭合 |
| gateway_users(team_handle: neon_bbp)/report_retest_user | []/null | 闭合 |
| **AssetContext**(asset_identifier+program_handle) | 真实 program(neon/figma/security)恒 500;不存在 program → 200 null | **角色限制**:类型登录态 introspection 可见(匿名不可见=角色裁剪)含 compensatingControls/dataSensitivitySignals/environmentSignals/multiTenantSignals/severitySignals 富字段,但非 member 不可达(500 无内容) |

**结论:漏网字段全部闭合** — node loader 同权限、team 工具非 member 恒 500(无 oracle)、AssetContext 角色限制;行为模式 = 内部 policy 检查抛 STANDARD_ERROR vs 值级 null 化两种防护并存

## AI 配置面收尾(AA-AE 组,2026-09-08 续,登录态)——hai_plays 活面深测

**发现**:hai_plays(114 根字段清单补扫时未测字段之一)对 hacker 返回 1 条 system play = HaiPlay/486 "Hai for Hackers"/"Your hacker security agent"(平台给 hacker 的默认 AI agent)

| 测试 | 结果 | 判读 |
|---|---|---|
| HaiPlay introspection | 17 字段含 instructions/conversation_starters/routing_*/owner(HaiPlayOwnerUnion)/organizations | 登录态可见;匿名 introspection 返回 NULL(**角色裁剪实锤**:AssetContext/HaiPlay 均匿名不可见) |
| instructions(AC1) | NON_NULL 字段返回 null → 节点整体 null + 错误 | **字段级权限**(非 owner 不可读) |
| routing_enabled(AE2) | 同上 null | 敏感字段组(instructions/routing_*)统一字段级遮蔽 |
| system=true | 仅 486(名称/描述 UI 可见) | 行级过滤:system play 可见 |
| system=false / owner=neon_bbp/security / organizations={handle:neon_bbp} | 全空 | **行级过滤完整**,owner/org 过滤不可放宽 |
| total_count | 1 | 可见集确认 |
| hai_agent_core_config(s)/agent_guidance/custom_dashboard/clusters | null/[]/空连接 | 闭合 |
| oauth_application/tray_solution_instance_url | NOT_FOUND(错误消息泄漏模型名 Doorkeeper::Application/TeamIntegrations::Tray) | 无内容价值 |
| label_categories | 5 条(LabelCategory 1,2,3,4,7) | 全局元数据(公开字典) |

**结论:hai_plays 面 = 行级(仅 system)+ 字段级(敏感字段组 null)双防护 → 闭合**;114 根字段清单穷举完成(全部未测字段已测,无一可越权)

## mutation 通道面补测(AF-AS 组,2026-09-08 续,登录态 xxbo)——bundle 考古 + 753 mutation 全清单

**入口**:bundle 考古发现 /reports/${id}/export/raw|zip 真实形态(POST + JSON body {include_internal_activities, redact_usernames})→ 导出/分享/检测/订阅/收藏家族全测

| 通道 | 自己报告 | target 3732660 | 结论 |
|---|---|---|---|
| POST /reports/{id}/export/raw(导出全文 text/plain) | 200 全文(格式:Title/Scope/Weakness/Severity/Link/Date/By/Details) | 404 HTML | 行级过滤(与 .json 同内核) |
| POST /reports/{id}/export/zip | 200 application/zip(PK 头,含 <team>-<id>.txt) | 404 HTML | 行级过滤 |
| raw + include_internal_activities:true(自己) | **404**(参数合法但功能级拒) | — | 功能级权限:含内部活动仅 team |
| exportReportPdf mutation(report_id ID + email + pdf_type) | appropriate access(全部 pdf_type) | — | 角色级:reporter 无权 PDF 导出(枚举错误泄漏合法值 ["full","reporter","triage"]) |
| shareReportViaEmail(emails:[String!]) | appropriate access | An object was not found | **双检查顺序暴露**:可见性检查先于功能检查(不可见=not found;可见但无权=appropriate access) |
| detectSensitiveReportData(report_id ID + include_internal) | appropriate access | not found | 同上双检查;reporter 无权全内容敏感扫描 |
| updateReportSubscription(report_id Int!) | appropriate access | appropriate access(无差异) | 功能级拒(reporter 不能订阅;无 oracle) |
| updateReportFavorite(report_id ID + favorite) | **was_successful:true**(收藏可用) | not found | **行级可见性检查嵌入收藏路径** |
| executeHaiReportSummary/Statistics/Assessment | — | input 无 report_id,是 Submit-with-Hai 写型工具(organization_id+summary/evidence/question 输入) | 非读取器,无越权读面 |

**753 mutation 全清单(607 去重)已获取**(__type Mutation fields+args);高价值 input 结构 introspection 完成:DetectSensitiveReportDataInput/UpdateReportSubscriptionInput/LinkReportInput/CreateHaiChatInput/CreateHaiReportDataInput/CreateHaiTaskInput/ResumeHaiTaskInput/NewConversationInput(LlmConversationContextInputType 含 **report_ids:[Int!]**)/MessageReportAssistantInput/UpdateReportFavoriteInput/RequestReportDisclosureInput/CreateReportIntentV2Input/UpdateViewingReportInput/ToggleHaiInput

**本轮新指纹**:
- __type 别名限制:同一 selection set 内 __type 最多 3 个(批量 introspection 须分批)
- ID 类型参数须 gid 完整形态(裸数字 → "An object was not found")
- export 权限分三层:REST raw/zip 行级(reporter 可用自己报告);exportReportPdf/share/detect/subscription 功能级/角色级(reporter 全拒)
- **updateReportFavorite 对照实验证明 mutation 层与查询层共享同一可见性内核**(自己 success/target not found)

**结论:mutation 通道面全部闭合**——导出/分享/检测/订阅/收藏全家族无越权;防御 = 行级可见性检查(所有含 report_id 的 mutation 入口)+ 功能级权限(reporter 仅部分功能可用)双检查统一。AI 执行器家族非报告读取器(内容输入型)。

## Backbone 老 REST + AI/Hai 通道终测(AV-BF 组,2026-09-08 收尾,登录态 xxbo)

**触发**:信息员渠道确认存在"有人提了越权读报告的报告"(私有不公开)→ 全量重扫 bundle url: strings 老端点 + 从未实操的 AI 会话链

### Backbone 老端点(subscription.json/public_view/hackbot 家族)
| 端点 | 结果 | 判读 |
|---|---|---|---|
| GET /reports/{id}/subscription.json?subscribe= | 404 HTML(自己/target) | 路由仅 POST |
| POST /reports/3992341/subscription.json?subscribe=true\|false(自己) | **200 完整报告 JSON**(id/global_id/title/state/severity/reporter/team) | 老订阅端点活(POST),响应=报告全文 JSON 形态 |
| POST /reports/3732660/subscription.json(target,query/body/form 编码/真/假) | 恒 404 text/plain(与 .json 同款控制器权限 404) | 行级过滤与 .json 同内核;回滚成功(AX5) |
| public_view GET/POST(自己/target) | 404 HTML | 路由死 |
| hackbot/accept GET/POST | 404 HTML | 路由死 |
| /hacker_reviews GET | 200 [] | 活端点空(自己无 reviews) |
| /user/csrf GET | 200 {csrf-token} | 正常功能 |
| GET bugs.json?organization_inbox_handle=(neon/hackerone/security) | 404 HTML | GET 路由死 |
| POST bugs.json form organization_inbox_handle=neon | 200 count=0 | 参数忽略或 org 非有效 |
| organizations(where:{handle:{_eq:...}}) | nodes:[] | org 查询按成员过滤(xxbo 无 org);team.organization 字段 hacker 视角 null |

**结论:Backbone 老 REST 面与 GraphQL 同权限内核,全闭**(延迟差异 AW2 2.8s 为瞬态,复测无稳定差异)

### AI/Hai 通道链(newConversation → copilot)——2026-09-08 最大新面

**链结构**(introspection):NewConversationInput{clientMutationId, context_object: LlmConversationContextInputType(可空), hai_play_id(可空), sign_post_name};LlmConversationContextInputType{report_ids:[Int!], team_handles, pentest_opportunity_id, organization_id/name, path, route, dry_run};CopilotInput{llm_conversation_id: ID! 必填, message: String! 必填};LlmConversationMessage{author USER/ASSISTANT, state, content_blocks{text/thinking/type}, message_index};HaiPlay 486 = "Hai for Hackers"(system play,默认)

| 测试 | 结果 |
|---|---|
| newConversation(report_ids:[3992341] 自己) | **success**,LlmConversation/7312353 |
| newConversation(report_ids:[3732660] **target**) | **success**,LlmConversation/7312354——**会话创建无可见性检查!** |
| newConversation(空 input) | 500 |
| copilot(自己会话,"总结报告内容") | success,AI 回复:"report 3992341 is loaded but organization 未启用 Hai"——**Hai program 级 gate** |
| copilot(target 会话,同上) | success,AI 回复:尝试读 3732660 报 **"doesn't exist or insufficient permissions"**——读取工具以后端用户身份做可见性检查 |
| copilot(target 会话,给 URL 让 AI 读) | AI:"I can't open URLs... attempting access got error"——确认读取工具存在且被权限拒(非幻觉,AI 明说 attempt) |
| 对照:2487889(公开)/3932185(自己 Vercel dup)/3951926(自己 Figma dup) 三会话 | **全拒**:公开=Hai 未启用 gate;自己 Vercel/Figma=权限错误(closed dup 后 AI 通道也读不了) |
| context 注入确认:问"哪个报告加载了" | AI 准确答 report_ids(3732660/3992341)= **context.report_ids 服务端注入 AI 系统提示**;但读取另有 gate |
| node(id: gid) 查询会话消息 | 可用(ConversationUnion 6 类型不含 LlmConversation;conversation(id:) 只覆盖 6 agent 会话类型;LlmConversation 走 node() 通用查询) |
| deleteConversation | 不存在(会话无法 API 删除,UI 可能可清) |

**AI 通道防御架构(2026-09 实测)**:
1. **Hai 启用 gate**:program/org 未启用 Hai → AI 拒绝读该 org 报告(连公开报告都拒)
2. **可见性 gate**:AI 报告读取工具以**当前用户身份**执行 load_report 权限检查(target 3732660 明确拒绝)
3. 会话壳(newConversation)可对任意 report_ids 创建成功 = **无数据流出**(空会话,消息层 gate 生效)→ 非洞
4. 错误文案三型扩展:not found(遮蔽)/appropriate access/Insufficient permissions + **Hai 未启用**(program gate) |

**结论:AI/Hai 通道闭合**——双重 gate 与 GraphQL 查询层同族;newConversation 无检查但无泄漏面。信息员线索在 hacker 角色可见读取面上无法复现 → 洞型应在写面/host 级/其它角色上下文(超出当前纪律与账号能力) |

## 渲染层/资源层/导出面终测(BH-BO 组,2026-09-08 收尾,登录态 xxbo)

**触发**:用户质疑"非按他们接口走" → 打老 Rails 渲染层/SEO 协议/CDN/资源域/导出面

| 面 | 结果 | 判读 |
|---|---|---|---|
| GET /reports/{id}(登录态裸页面) | target/242816 = **403 "Oops! You can't access this report because it isn't public yet"**(Rails 老页,controller_reports action_show);不存在=404;自己/公开=200 SPA 壳 | **页面层 403/404 区分存在性**(oracle);og:title 仅有权者,og:description 仅公开披露(2487889/4000158 有、3992341 无),403 页零报告信息 |
| ?format=html/no_js/layout/preview/share/_escaped_fragment_ | 全 403 同款(无渲染差异) | Rails SEO 层无缝隙 |
| .pdf/export 页/download | 404 路由死 | |
| /reports/{id}.json vs 页面 | .json 404 text/plain(API 控制器)vs 页面 403 HTML(页面控制器)——两种控制器同拒 | |
| GET /graphql?query= | 404(GET 路由死,仅 POST) | |
| .atom/.rss/.pdf(hacktivity/program/neon) | 404 或 SPA 壳 | feed 路由死 |
| CSP 头泄漏 host:api.hackerone.com(Basic 401 匿名活)/chat-agent(DNS 无)/a5s.hackerone-ext-content.com+integration-configuration(S3 静态)/errors.hackerone.net(403) | 附件 S3 桶名:hackerone-us-west-2-production-attachments | api.hackerone.com 需 token(用户账号暂不支持);其余无数据面 |
| CDN | Cloudflare + no-store + user-authenticated 头 | 缓存面关闭 |
| 753 mutation 文档串重扫(48 读取语义名) | exportLifetimeReports(handle+email 导出 program 全史)= 非 member 全 AUTHORIZATION 拒;不存在 handle = "team should not be nil"(ARGUMENT);previewRedactReport/updateReportTitleShow 字段名不存在(更新提示 updateReportTitle) | 导出面成员校验在位 |

**结论:渲染层/SEO/导出面全闭**——页面层存在性 oracle(403 vs 404)为唯一差异(无内容);导出类 mutation 成员校验。信息员线索全部闭合:主站 hacker 角色所有读取/导出/AI/老代码面均与 GraphQL 同权限内核 |

## 技术笔记(复用)
- /graphql POST 需 CSRF:从页面 `meta[name="csrf-token"]` 取值,header `X-CSRF-Token`(匿名无会话反而不需要)
- 浏览器执行通道:fetch 同源自动带 cookie;结果用 textarea DOM 注入(fixed 定位)+ focus/select 供用户 Ctrl+C(alert 不可复制,console.log 用户环境不可见,copy() 不存在)
- 报告 id:数据库整型;GraphQL 全局 id 为 base64(Z2lkOi8v...)
- 错误格式:extensions.code = undefinedField(字段不存在)/ typeName 泄漏类型名
- Neon 项目 handle = neon_bbp
- 根查询 reports 同时支持 Hasura where 语法与 database_id/edges 风格(不同前端模块)

## 测试产物
- _h1x10_fields.py 匿名字段枚举 / _h1x12_anonids.py 匿名批量查编号 / _h1x13_dupfields.py duplicate 字段静态分析 / _h1x14_track_frag.py fragment 追踪
- h1x49 系列:_h1x49b_sqli.py where 谓词注入 / _h1x49c_sqli2.py 超时复测+order_by 类型 / _h1x49d_sqli3.py 端点探测+ES 首探 / _h1x49e_es_fields.py ES 字段白名单枚举 / _h1x49f_es_bound.py 索引边界 / _h1x49g_es_vals.py 字段值格式 / _h1x49h/j 节点读取 / _h1x49k_sqli_roots.py 根查询参数注入 / _h1x49l_reports_handle.py 收尾
- 会话内浏览器 GraphQL 查询记录见对话历史(CSRF token 即时获取,无持久凭据存储)
