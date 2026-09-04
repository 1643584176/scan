# Neon postgres 平台库横切审计归档（lakebase_attributes 写面 + auth.uid 伪造）

- 日期:2026-09-03
- 环境:Neon staging 直连 PG（ep-crimson-fog-w2gucld1）
- 背景:pg_repack 链闭合后,继续深挖数据库面;发现用户可连 **postgres 平台库**

## 1. 关键事实链

- neondb_owner 可连 postgres 库（datacl None → PUBLIC CONNECT 默认）
- pg_read_all_data/pg_write_all_data（经 neon_superuser 二级继承）**跨库生效**,覆盖 postgres 库
- postgres 库平台对象:neon schema（遥测视图群,owner=cloud_admin）、public.health_check、
  public.lakebase_attributes、neon_migration.migration_id

## 2. 平台写保护机制与不一致（核心发现）

- health_check / migration_id:BEFORE INSERT/UPDATE/DELETE/TRUNCATE FOR EACH STATEMENT 触发器
  `neon_health_check_superuser_check` / `neon_migration_id_superuser_check`
  → 执行 `neon.neon_check_for_superuser()`(plpgsql,查 pg_roles.rolsuper,非 superuser 即 RAISE 42501)
- **lakebase_attributes:无触发器/规则/RLS**(relhastriggers=False, relhasrules=False)
  → 用户实测可 INSERT(事务回滚验证)/UPDATE(no-op)/DELETE(0 行条件) 全成功
- 约束仅 name NOT NULL PK + last_updated NOT NULL,无值域 CHECK
- pg_stat_statements 轨迹证明:平台 migration 曾 `INSERT INTO lakebase_attributes(name,value,last_updated)
  VALUES($1,$2,now())`(1 次)并对该表执行 no-op UPDATE 探测(`SET value=value WHERE $1=$2`)——
  平台有保护探测框架但该表**未加触发器**(health_check/migration_id 有对应 DO 块确保)
- postgres 库 public schema 用户不可 CREATE TABLE(有基础防护,此表为漏网)

## 3. auth.uid() 伪造(降级路径)

- pg_session_jwt 0.5.0 源码审计(src/lib.rs + gucs.rs,本地 _pg_session_jwt_src):
  - `pg_session_jwt.jwk`:GucContext::**Backend**(仅连接启动注入,用户不可 SET)→ 验签公钥
  - `pg_session_jwt.jwt` / `request.jwt.claims`:GucContext::**Userset**(用户可 SET)
  - `session()/user_id()/jwt()`:当 `NEON_AUTH_JWK.get().is_none()` 时**跳过验签**,
    直接解析 request.jwt.claims 的 sub claim
- 实测:直连 jwk GUC = **None(未注入!)** → `SET request.jwt.claims='{"sub":"0000...0001",
  "role":"authenticated"}'` 后 `auth.uid()` 返回伪造 UUID、`auth.session()` 返回伪造 claims
- 源码注释:"Generated per connection by Neon local proxy"——设计意图是注入,staging 实测未注入
  = 实现与设计不一致
- 影响边界:消费方 = 用户自建表的 RLS 策略(auth.uid()=owner_id 模板)→ 单租户自影响
  (neondb 库无平台 RLS 表,neon_auth 表 RLS 全关)→ **Low/N-A**
- 若平台注入 jwk 该面即关闭;若未来出现平台 RLS 表则升级为真实漏洞

## 4. 其他旁路(记录)

- neon schema 遥测视图全可读(neon_backend_perf_counters 37627 行等)——本 compute 性能指标,低敏
- pg_stat_statements 可读(平台 SQL 轨迹)——监控 SQL 为主,无敏感逻辑
- neon schema 25 函数 PUBLIC EXECUTE(replace_hll/neon_clear_lfc/prewarm_local_cache/cancel_prewarm 等)
  副作用仅影响自 compute 缓存/统计;危险类(neon_emit_reverse_etl_commit/pg_resize_shared_buffers/
  reset_perf_counter/prewarm_buffer_cache)已 revoke 为 cloud_admin-only
- postgres 库无 cron schema(job 表不存在);pg_cron scheduler 进程存在但 idle
- 平台进程:compute_ctl:compute_monitor / vm-monitor / neon_compute_sql_exporter(cloud_admin)

## 5. 脚本索引

- _pg22_full_audit.py 全库对象图景(schema/表/RLS/ACL/definer)
- _pg23_hidden_schemas.py auth/pgrst schema 对象(pg_session_jwt 函数层)+ 多库探测
- _pg24_postgres_db.py postgres 库首连:neon 视图/lakebase/health_check/migration
- _pg25_lakebase.py 平台对象结构 + 视图可读性
- _pg26_lakebase_write.py lakebase INSERT(回滚)成功 + 保护表对比
- _pg27_platform_guard.py 触发器机制暴露(neon_check_for_superuser)
- _pg28_fn_acl.py 函数 proacl 分级(9 cloud_admin-only vs 25 PUBLIC)
- _pg29_public_fns.py PUBLIC 函数清单 + 平台进程观察 + lakebase n_tup_ins=1
- _pg30_cron_platform.py cron schema 否定 + pss 列结构
- _pg31_pss_v2.py 平台 SQL 轨迹(migration INSERT lakebase 证据)
- _pg32_auth_guc.py **auth.uid 伪造实测 + lakebase DELETE + CREATE 权限否定**

## 6. 残留与零破坏

- 全部测试事务回滚/no-op/0 行条件;k_probe_t 未创建成功(权限拒绝)
- postgres 库无任何测试残留;neondb 库 k_* 对象零残留(此前已验)

## 7. 方向 1 追底:lakebase_attributes 消费方(结论:无活跃消费方)

- console bundle(app.js)证据:Lakebase = **Databricks 产品**(基于 Neon 技术),feature flags 为
  databricks.lakebase.* / databricks.fe.lakebase.*(HA/snapshots/CU resize 等)——Neon staging 的
  该表是 Lakebase 集成前置表(Databricks 方向)
- pg_stat_statements:表创建后 migration INSERT 1 行(n_tup_ins=1,现 0 行)并对该表跑过
  no-op UPDATE 探测——**平台有保护探测框架但未加触发器**
- 当前无任何进程活跃读该表(平台进程 SQL 轨迹无读);影响 = 条件性(待 Lakebase 功能启用)
- postgres 库 public/neon/neon_migration schema 用户均不可 CREATE(干扰 migration 面不存在)

## 8. 方向 2 追底:auth.uid 伪造消费方(结论:零消费方,N/A)

- postgres 库:0 RLS 策略;neondb 库:0 RLS 策略、0 RLS 表(demo_rls 已清理)
- 无任何对象依赖 auth schema 函数(pg_depend 查询空);无函数体引用 auth.*
- → auth.uid()/session() 伪造在当前两库无任何消费方;影响限于用户未来自建 RLS 表(单租户自影响)
- data-api 侧:PostgREST 每请求 SET ROLE + 覆盖 request.jwt.claims,匿名/authenticated 请求不可篡改;
  直连者可篡改但数据本是自己的 → 跨用户场景在单租户架构下不成立

## 9. 候选报告评估

| 发现 | 证据强度 | 影响 | 提交价值 |
|---|---|---|---|
| lakebase_attributes 无 superuser 保护可写 | 强(触发器对比+I/U/D 实测+migration 轨迹) | 无活跃消费方,条件性(Lakebase 功能启用后) | 中低(Low,防御不一致) |
| auth.uid() 伪造(jwk 未注入) | 强(源码+实测) | 零消费方,单租户自影响 | 低(N-A) |
