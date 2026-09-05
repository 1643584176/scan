# -*- coding: utf-8 -*-
"""append ch14 (V29 isolation boundary) to Neon auth report"""
p = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
ch = """

---

## 14. 隔离边界全景：能否看到"其他人"的数据（V29, 2026-09-05）

> 触发：用户追问"只能查到自己数据吗，可以看其他人的数据吗"。对 DB 实例/角色/权限链/分支复制
> 做全景扫描，验证租户隔离边界。

### 14.1 实例级扫描结果

| 面 | 结果 | 判定 |
|---|---|---|
| pg_database | 仅 neondb/postgres/template0/template1（全部 7-10MB，无他人库） | 项目级物理隔离 ✓ |
| pg_roles（实例级） | NeonDb_Owner/anonymous/authenticated/authenticator/cloud_admin/neon_auth/neon_service/neon_superuser/neondb_owner——**平台标准角色模板**（每项目一致），无其他租户角色 | 无跨租户 ✓ |
| pg_stat_activity | 仅 cloud_admin（平台监控，idle）+ neon_auth（auth 服务写 session）+ 我自己的查询 | 无他人活动 ✓ |
| schemas/tables | neon_auth 9 表 + public 残留（已清） | 仅自己 schema ✓ |

### 14.2 权限链真相（修正第 12 章"表权限仅授 owner"表述）

- **neon_auth 9 表 owner = neon_auth role**（auth 服务专用），role_table_grants 显式授权也仅授 neon_auth
- **neondb_owner（项目 owner）∈ neon_auth 成员** ← 我能读写 auth 表的通道 = 平台显式设计（owner 管理自身 auth 数据）
- neondb_owner ∈ neon_superuser（createrole 能力来源）∈ anonymous/authenticated（Data API PostgREST 角色组）
- neon_service ∈ neon_auth（平台服务可扮演 auth role）
- 低权限测试 role 对 neon_auth 读写全 DENY（V26 已验证）→ **无任何低权限→auth 数据通道**

### 14.3 分支复制验证（v29iso 分支，只读）

- 从 main 创建分支 br-raspy-snow-w2n12fvw → 内容 = main 的完整 auth 快照：11 用户（全部为本项目注册的测试邮箱 libobo1229+*）、118 session、14 verification、1 jwks、project_config 1 行 → **无任何非本项目用户/平台数据混入**
- 分支复制 = 自身数据拷贝（与官方 "branchable identity" 文档一致）；检查后仅删除 endpoint（计算节点），分支本体保留

### 14.4 结论：看不到其他人的数据

项目级物理隔离（独立 compute/storage + 平台标准角色模板），实例内无其他租户库/角色/活动；
auth 数据（user/session/account/verification/jwks/project_config）仅含本项目内容；
唯一"实例级共享"对象为平台角色（cloud_admin 等）与模板库——均不可达不可用。
**跨租户/跨项目数据面不存在 → 无洞。**

### 14.5 环境状态与残留记录（Informational）

- 清理：public.v8probe_galywj（owner=neondb_owner，V8 轮探针表）已 DROP；pwn role（本人测试残留）已 DROP
- **不可清理对象**：role `x"; CREATE ROLE pwn LOGIN; --`（V 系列早期某轮注入载荷名角色，login=True 但无密码）
  - neondb_owner 对其无 ADMIN option → DROP/GRANT 均被平台拒绝（PG 权限保护生效，归属不明对象不可被 owner 删除——正确行为）
  - 无法认证登录（无密码）、无成员关系、不持有任何对象 → 无实际风险；留档备查
- v29iso 分支（br-raspy-snow-w2n12fvw）保留未删（内容已验证全为本项目测试数据；是否删除待用户决定）
"""
with open(p, "a", encoding="utf-8") as f:
    f.write(ch)
print("appended, now %d lines" % len(open(p, encoding="utf-8").readlines()))
