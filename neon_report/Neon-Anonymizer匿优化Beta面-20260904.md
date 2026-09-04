# Neon Anonymizer 匿优化分支 Beta 面测试（2026-09-04）

> 阶段：续 Auth/DataAPI 技术面之后（_nz01~_nz37），目标=OpenAPI 未测端点的"换角度"挖掘
> 端点：POST /projects/{pid}/branch_anonymized（Beta）+ /anonymize + /masking_rules + /anonymized_status
> 合规：X-Bug-Bounty: xxbo；零破坏（分支即建即删/源数据未动）；测试账号 libobo1229（staging）

## 1. 触发背景

本地 spec（09-03）里 Branch/Snapshot 等 tag 存在大量未测端点，其中最值得挖的是
**匿优化分支**（PostgreSQL Anonymizer 静态脱敏 Beta 面）：控制面新建分支副本 + 平台自动
应用脱敏规则。攻击假设：#3992341（pg_repack SECURITY DEFINER 钩子）同源——若脱敏作业
以特权角色执行且 masking 规则允许租户可控代码 → 平台上下文任意 SQL。

## 2. 全流程走通（功能面）

| 步骤 | 端点 | 结果 |
|---|---|---|
| 创建+规则 | POST /branch_anonymized | 201；fork 源分支 + endpoint；restricted_actions（restore/delete-rw-endpoint/connect-to-endpoints 禁）|
| 初始化 | （自动）| state=initialized："Successfully initialized PostgreSQL Anonymizer on all databases" |
| 启动脱敏 | POST /branches/{bid}/anonymize | initialized 态 405（不能重复 start）；**anonymized 态 200 可重跑** |
| 规则管理 | GET/PATCH /masking_rules | 200；PATCH 全量替换语义 |
| 状态监控 | GET /anonymized_status | 200；state/status_message/last_run（triggered_by=console 用户 id）|
| 分支创建时直接触发 | body start_anonymization=true | 6s 内完成（masked_columns 计数）|

- 脱敏正确性：email 列 → anon.fake_email() 全 fake（cweber@example.com 等）；无规则列不动
- copy-on-write 隔离：源分支数据全程未污染（多次验证）✓
- 组合规则：PATCH 追加 full_name=anon.fake_last_name() → 重跑 masked_columns=2 ✓

## 3. ★ 执行上下文验证（核心安全结论）

**探针设计**：自定义函数记录 current_user/session_user/rolsuper 到日志表 →
作为 masking_function 提交 → 读脱敏结果判断执行角色。

**防线 1：anon 2.5.1 TRUSTED 机制（自定义函数面闭合）**
- pg_trusted_functions 视图：仅 pg_catalog 36 个纯函数（left/right/md5/random/regexp_replace/
  concat/now/to_json…全无副作用）
- anon.* 内部函数（anonymize_table 等）标 **UNTRUSTED**
- `SECURITY LABEL FOR anon ON FUNCTION/Schema IS 'TRUSTED'` → **only a superuser can set**
  （neondb_owner 被拒）→ 租户无法注册自定义 masking 函数
- 控制面 masking_function=自定义函数 → 400 "is not a valid label for a column"（设 label 时
  anon C 层校验函数存在+trusted）

**防线 2：表达式注入绕过可行但无特权**
- 本地实验：`MASKED WITH FUNCTION pg_catalog.concat(current_user::text)` LABEL OK +
  执行成功（列值=current_user）；**子查询可用**：`concat((select rolsuper::text ...))` 成功
- 控制面提交 masking_function='pg_catalog.concat(current_user::text)' → **API 201 接受** +
  脱敏完成 → 脱敏分支 email 列值 = **'neondb_owner'**
- PATCH 规则后重跑 → 再次 'neondb_owner'
- **结论：平台脱敏作业以 neondb_owner（租户 owner）连接执行，非 cloud_admin/superuser**
  → 表达式注入仅在租户 owner 上下文（自己能做的权限），无提权、无跨租户、无平台数据
- 注入点残余能力 = 把租户 owner 权限内的任意 SELECT 结果写入脱敏分支列（自读自写，无影响）

## 4. 附带发现（Informational，不报）

1. **幽灵分支副作用**：masking_function 无效（400 "not a valid label"）时 API 报 400，
   但**分支已被 fork + anon 已初始化**（两次独立复现：400 响应后项目里出现 anonymized 分支）
   ——状态不一致（客户端以为失败，实际消耗分支配额）；无安全影响
2. POST /anonymize 在 initialized 态 405（仅 anonymized/error 可重跑）——行为差异非洞
3. connection_uri 返回 channel_binding=require（psycopg3 直连失败需剔除参数）——兼容性细节

## 5. 环境残留

- 6 个测试分支（br1~br5 + 2 幽灵）全部 DELETE 200；源分支仅剩 main
- 源分支测试对象（sbx_anon_src/sbx_probe_log/sbx_probe_fn/mk_fn + anon seclabel）全 DROP
- roles 残留 x"; CREATE ROLE pwn LOGIN; -- 与 NeonDb_Owner（09-03 历史测试遗留）未动，待统一清理

## 6. 结论

- **无新洞**。匿优化 Beta 面实现安全：扩展以租户 owner 安装、脱敏作业以租户 owner 执行、
  自定义函数 TRUSTED 仅 superuser 可设、表达式注入无特权上下文
- 方法论收获：anon TRUSTED 机制 = 平台对 masking 面注入的纵深防御；执行角色验证法
  （concat(current_user::text) 侧信道）可复用于其他平台"作业执行上下文"类黑盒验证
