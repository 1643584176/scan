# Neon 方向B：Beta 新面系统性测试闭合 - 20260905

> 背景：方向A/B 双线之一（B = Neon DB 侧找新洞，不与 #3992341 重复）。
> 本报告覆盖 2026-09-05 一轮新增测试（S2~S6），与 09-03/04 既有报告无重叠。

## 结论摘要

**未发现新的可利用漏洞。** 跨项目/跨分支资源隔离在所有新测面上均正确执行
（统一 404/400 拦截模式），数据面（S3/AI Gateway）在 staging 不可达（403），
无法进一步测试。staging 为纯单用户环境（无 shared project、单 org、单成员），
跨用户 IDOR 无测试载体。

## 测试载体

| 载体 | 值 | 用途 |
|---|---|---|
| PA | orange-sun-90493739 / main: br-wandering-field-w2ob6mpn | 构造测试（临时分支/快照/桶） |
| PB | damp-term-63384673 / production: br-raspy-band-w247957z | 干净跨项目靶 |
| 凭据 | API key (napi_*), X-Bug-Bounty: xxbo | console-stage.neon.build |

## 攻击假设矩阵与结果

### S2 Snapshot/restore 两步状态机（7 端点 + backup_schedule）

| # | 假设 | 请求 | 结果 |
|---|---|---|---|
| H1a | path 项目与他项目 snapshot 不匹配 | POST /projects/PB/snapshots/{sid_PA}/restore | 404（按 project 过滤） |
| H1b | restore target_branch_id 跨项目 | POST .../PA/snapshots/{sid}/restore {target: brB_tmp} | **400 "target branch is from another project"** |
| H1c | 一步模式绕过 | 同上 + finalize_restore=true | **400 同样拦截** |
| H2 | 两步窗口期越权 | restore(false) 后观察源/目标分支 | 正常：restore 预览分支独立（restored_as 记录），finalize 只作用于 restore 分支 |
| H3a | PATCH snapshot 跨项目 | PATCH /projects/PB/snapshots/{sid_PA} | 404 "snapshot not found"；name 未变 |
| H5 | backup_schedule 跨项目读写 | GET/PUT path(PA)+brB | GET 空 schedule；PUT 404（功能未启用 staging） |

### S3 roles / Consumption / restore 一步模式

| # | 假设 | 结果 |
|---|---|---|
| B | reveal/reset_password 跨项目 branch 引用 | 404 "branch not found; branch_id..., project_id..."（**(project,branch) 联合查询**） |
| C | restore 一步跨项目 | 400（与两步同校验） |
| D | Consumption 参数 | 需 from/to/project_ids；错误消息含操作名（无害） |
| A | 侦察 | shared projects=空 / 单 org free / 单成员 admin —— **无跨用户载体** |

### S4 Credentials / AI Gateway / Storage / Logs

| # | 假设 | 结果 |
|---|---|---|
| - | issue scoped credential | 201；scope 白名单严格：`admin:*`→400 invalid value，空→400 |
| - | reveal 跨项目（path=PB+PA token） | 404 "credential or project not found" |
| - | reveal 跨分支（path=PA+PB branch） | 404 "branch not found in this project" |
| - | rotate 跨项目 | 404 |
| - | AI Gateway / Storage 状态 | enabled；base_url/s3_endpoint 绑定分支 subdomain |
| - | Logs fields/query 跨项目 | 404 LOGS_NOT_AVAILABLE |

### S5 Buckets（branchable object storage，Beta）

| # | 假设 | 结果 |
|---|---|---|
| I1 | 跨项目 bucket 引用（download/presign） | 404 "bucket not found; project_id..., branch_id..."；**key 日志 sha256 redaction**（`key_redacted:"len=9 sha256=..."`） |
| I2 | object_key 路径穿越（5 种编码） | 全 404（参数化 key 查询）；绝对路径风格→"this route does not exist" |
| I3 | public_read 匿名读 / 私有桶隔离 | 数据面 403（nginx）——**环境不可测** |
| I4 | AI base_url 跨分支鉴权 | 403（数据面整体不可达） |

## 防御架构观察（正面，供报告背景参考）

1. 所有资源操作采用 (project_id, branch_id) **联合查询**，跨项目引用统一 404，不泄露资源存在性
2. restore target branch 归属**显式校验**（400 明确错误信息）
3. 凭据 scope **白名单严格校验**（未知 scope 拒绝）
4. presign 错误日志对 object_key 做 **sha256 redaction**（防 key 泄露）
5. logs 用专用错误码 LOGS_NOT_AVAILABLE
6. 数据面（S3/AI）nginx 层 403——staging 未开放直连
7. create snapshot 用 query 参数而非 body（参数面小）

## 环境限制（记录）

- staging 纯单用户：无 shared project、单 org、单成员 → 跨用户 IDOR 不可测
- 数据面（presign 直传、S3 匿名读、AI /v1/models、AI invoke）全部 403 → 仅控制面可测
- backup_schedule PUT 未启用（404 "not enabled for this project"）
- 测试残留（已清理）：PA main 上历史 role 残留（`x"; CREATE ROLE pwn LOGIN; --`、`NeonDb_Owner`，09-03 早期测试产物，无害，记录备查）

## 结论与建议

方向 B（Neon DB/控制面新洞）在可测范围内**已闭合**：
- 跨项目/跨分支隔离：全 404/400 正确
- 两步状态机：无窗口漏洞
- 凭据/scope：白名单 + 联合查询
- 剩余理论面：① 扩展源码级审计（低 ROI）② 生产面（需邮件协调）③ 数据面（staging 不可达，需 prod 载体）

**建议转向**：方向 A（H1 其他数据库项目）或等待生产面协调后测数据面（S3 匿名读、
AI Gateway invoke、presign 直传链路——这些是唯一未被覆盖的传输面）。
