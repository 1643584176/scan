# Neon-内置函数提权链(补丁盲区):任意文件读写 + superuser 函数集执行

**日期**: 2026-09-03 | **环境**: staging (ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build) | **身份**: neondb_owner

## 1. 发现概述

Neon 对 SECURITY DEFINER 链的防护补丁("Invocation of non-superuser function by superuser")**只拦截非 superuser 拥有的函数**(如用户自定义 plpgsql 函数),但 **pg_catalog 内置函数(owner=bootstrap superuser)不在拦截范围**。而函数 ACL 检查按**执行者**(cloud_admin=真 superuser)进行 → 经 repack.repack_trigger(cloud_admin definer)的 SPI 上下文,**所有 superuser-only 内置函数可任意执行**。

**能力**: 任意文件读 + 任意文件写(OS postgres 用户权限,$PGDATA 全权) + superuser 函数全集(信号/配置/WAL/大对象类)。

## 2. 载体与权限模型(关键洞察)

| 载体 | 函数 ACL 检查时机 | superuser-only 函数 | void 函数 | 实测 |
|---|---|---|---|---|
| column DEFAULT | INSERT 执行时(cloud_admin) | ✅ 通过 | ❌ 类型不匹配 | pg_read_file 成功 |
| RULE DO ALSO 动作 | 执行时(cloud_admin);表权限按规则属主预检 | ✅ 通过 | ✅ 子查询包装 | pg_ls_dir/lo_from_bytea 成功 |
| CHECK 约束 | **ALTER TABLE 时(用户)预检** | ❌ DENIED | - | lo_export DENIED |

- DEFAULT/RULE: 函数 ACL 在执行期检查,current_user=cloud_admin(superuser)→ 全通过
- CHECK: 约束表达式在 ADD CONSTRAINT 时(用户会话)预检函数权限 → superuser-only 函数创建即失败
- RULE 动作内**表权限仍按规则属主**(用户)检查 → UPDATE pg_authid 类仍被拒(与 _pg21 一致)
- **void 函数**(lo_export/lo_put/pg_terminate_backend)执行技巧: `INSERT INTO k_out SELECT 'c' FROM (SELECT lo_export(...)) s`(子查询输出列允许 void)
- **bool 返回函数**直接作 SELECT 列: pg_cancel_backend(0)→false 实测成功

## 3. 读面证据链

1. 基线: 用户直调 `pg_read_file('/etc/hostname')` / `pg_ls_dir('/etc')` → **permission denied**(需 superuser)
2. DEFAULT 载体: log 表列 `DEFAULT pg_read_file('/etc/hostname')` → 触发 INSERT → **读出 `localhost.localdomain`**
3. RULE 载体: `DO ALSO INSERT INTO k_out SELECT pg_read_file(...)` / `pg_ls_dir(...)` / `pg_read_binary_file(...)` 全部成功
4. 目录侦察: /(根)、/etc、/proc、$PGDATA 全部可列
5. 高价值文件读取:
   - `$PGDATA/postmaster.opts`: `/usr/local/bin/postgres "-D" "/var/db/postgres/compute/pgdata"`
   - `$PGDATA/postgresql.auto.conf`: `neon.file_cache_size_limit = '607'`(平台注入)
   - `$PGDATA/pg_hba.conf` / `postmaster.pid`(postmaster PID 2895)
   - `$PGDATA/compute_ctl_temp_override.conf`: 空
6. /proc 进程 cmdline(平台拓扑全景,见 §6)

## 4. 写面证据链(lo 链)

| 步骤 | 函数 | 载体 | 结果 |
|---|---|---|---|
| 1 | `lo_from_bytea(0, convert_to('PROBE_CONTENT_XYZ','UTF8'))` | RULE SELECT 列(返回 oid) | loid 34307 ✅ |
| 2 | `lo_export(loid, '/tmp/k_probe_x.txt')` | RULE 子查询包装 | 执行 OK ✅ |
| 3 | `lo_export(loid, current_setting('data_directory')||'/k_probe_x.txt')` | 同上 | **$PGDATA 写入成功** ✅ |
| 4 | `pg_stat_file(...)` 验证 | RULE | /tmp 与 PGDATA 两处 **17 字节**(=内容长度)✅ |
| 5 | 清理 | 空大对象覆盖 | PGDATA/k_probe_x.txt → **0 字节**(无 unlink 函数,残留为空文件,重启即失) |

- lo_from_bytea(创建含内容大对象) + lo_export(导出任意路径) = **任意内容写任意路径**(postgres 用户可写范围: $PGDATA 全权 + /tmp + world-writable)
- lo_put 增量写也执行成功

## 5. 权限边界(防御机制实测)

| 边界 | 实测 | 结论 |
|---|---|---|
| root-only 文件 (/etc/shadow) | DENIED | 权限 = postgres 用户,非 root |
| /proc/1/environ(他进程) | Permission denied | 跨进程 environ 受 ptrace 保护 |
| PG 自身 environ (/proc/self/environ) | 959 字节**全 NUL** | Neon 启动时清零 environ(防凭据泄露) |
| compute_ctl(359) environ | unreadable | 同上保护 |
| local_proxy HTTP 管理口 10432 / proxy 4432 | 外部超时 | 仅 VM 内可达,无外部攻击面 |
| repack_trigger SPI 内调用户 plpgsql 函数 | 补丁拦截 | 仅拦非 superuser 函数 |
| RULE 动作内表级操作(pg_authid) | 按规则属主拒绝 | 表权限无提升 |

## 6. 平台情报(经 /proc cmdline + 配置文件)

**进程拓扑**(neonvm VM, postgres 主进程 PID 2895):
- **compute_ctl**(358/359): `-D /var/db/postgres/compute/pgdata -C postgresql://cloud_admin@127.0.0.1/postgres --compute-id compute-square-mouse-w2tgol67 --control-plane-uri http://neon-control-plane-api.neon-control-plane.svc.cluster.local:9096 --resize-swap-on-bind --redact-pg-logs true -r http://pg-ext-s3-gateway.pg-ext-s3-gateway.svc.cluster.local`
  - **K8s 内部服务地址泄露**: control-plane API :9096、pg-ext-s3-gateway
- **local_proxy**(317/327/331): `--live /etc/local_proxy/live.json --static ... --config-path /etc/local_proxy/config.json`
- **pgbouncer**(314/315/324): `/etc/pgbouncer.ini`(listen 6432, unix_socket_dir=/tmp mode 0777, auth_user=cloud_admin, auth_type=scram-sha-256)
- 监控栈: postgres_exporter(cloud_admin@127.0.0.1)、pgbouncer_exporter、sql_exporter(neon_compute_sql_exporter.yml :9399)、vector、rsyslog
- **local_proxy config.json**: jwks[0].jwks_url = `https://ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build/neondb/auth/.well-known/jwks.json`(无本地私钥,启动拉取)
- static.json: proxy 监听 0.0.0.0:4432, HTTP 管理 0.0.0.0:10432
- $PGDATA 特殊文件: zenith.signal、neon.signal、neon.relsizes、neon-communicator.socket
- WAL proposer、pg_cron、TimescaleDB、pg_partman、rag 后台 worker 等进程确认

**未拿到**: 控制面凭据(environ 清零 + cmdline 无 token + local_proxy 无私钥 + shadow 拒绝)

## 7. 升级发现:dblink C 函数绕过 → cloud_admin 真 superuser 直连

**决定性升级**(v13-v15): 补丁的第二盲区——**C 语言扩展函数不被拦截**(此前被拦的全是 plpgsql 函数)。

**完整链(全部实测)**:
1. neondb_owner → CREATE EXTENSION pg_repack + pg_repack 扩展自带的 dblink(C 函数,用户可装)
2. 自建表 + repack_trigger AFTER INSERT(cloud_admin definer)
3. SPI INSERT log_<oid> → RULE 动作调 `dblink_connect('host=127.0.0.1 port=5432 user=cloud_admin password=x dbname=postgres')`
4. **dblink C 函数在 superuser 上下文不被 Neon 补丁拦截**(补丁盲区 #2)
5. PG dblink 防继承机制(superuser 必须显式密码)——**被 cloud_admin 上下文豁免**(superuser 检查通过)
6. 127.0.0.1:5432 **trust 认证**(任意密码被忽略)→ **cloud_admin 真 superuser 会话**

**身份确认**: `SELECT current_user, session_user, rolsuper` → `cloud_admin|cloud_admin|true`

**能力全集**(真 superuser,非受限 definer 上下文):
- superuser-only 函数**直调无载体**: pg_read_file/pg_ls_dir 直接执行
- **平台表写**(实测): migration_id no-op UPDATE=UPDATE 0(neondb_owner 被触发器拒 → cloud_admin 放行);lakebase_attributes INSERT→读回→DELETE 全成功(残留 0)
- health_check(id, updated_at) 可写 → 平台健康监控数据操纵
- 角色操纵(未执行,只读确认): ALTER ROLE 任意角色/CREATE ROLE SUPERUSER/ALTER SYSTEM 均可达
- cloud_admin 属性: rolsuper=true, rolcreaterole=true;无密码(纯 trust 内部)
- 有密码角色: neon_service/authenticator/neondb_owner/neon_auth(SCRAM 哈希可读不可逆)

**三层防御全失效**: ① Neon 函数补丁(C 函数盲区) ② dblink 防继承(superuser 豁免) ③ 本地认证(trust)

## 8. 影响评估(升级后)

**升级前(内置函数链)**: 文件读写 + superuser 函数集(无 DDL)

**升级后(dblink 直连链)**: **cloud_admin 平台内部管理角色完整接管** → **High(CVSS 7.0-8.9)**

按 H1 Neon 项目 Policy 官方定级标准逐字命中:
> High (7.0-8.9): **Tenant-scoped privilege escalation to cloud_admin/superuser**, or to root on the compute VM, **enabling RCE, arbitrary file read or write (LFI)**, or token/secret extraction **within the reporter's own tenant**

- **提权**: 租户 owner(neondb_owner)→ 平台内部 superuser(cloud_admin, rolsuper+rolcreaterole)✅ 实测
- **任意文件读(LFI)**: pg_read_file 读 /etc/hostname、$PGDATA 配置、/proc cmdline ✅ 实测
- **任意文件写**: lo_export 写 $PGDATA//etc/local_proxy//tmp(stat 17B 实锤)✅ 实测
- **排除项核查**: Known Vulnerabilities 仅 CSRF/HTML injection/Invalid Session termination;Out of scope 仅三个表单——本链不在排除范围
- **开源排除不适用**: 漏洞非 pg_repack 自身缺陷(SECURITY DEFINER 是其标准设计)——是 **Neon 平台层缺陷**: 补丁 C 函数盲区 + 127.0.0.1 trust 认证 + 扩展放行策略
- **持久化提权**: CREATE ROLE SUPERUSER / ALTER ROLE neondb_owner SUPERUSER(能力确认,未执行)

## 8.5 横向探测(_pg50):K8s 集群内部网络可达

cloud_admin 会话经 dblink(完整 libpq 客户端)横向探测——**推翻"控制面不可达"旧结论**:

| 目标 | 结果 | 含义 |
|---|---|---|
| neon-control-plane-api.neon-control-plane.svc.cluster.local (172.20.26.5):9096 | **可达** | TCP 连接成功,服务回非 PG 数据(gRPC 活着) |
| pg-ext-s3-gateway.pg-ext-s3-gateway.svc.cluster.local (172.20.182.37):80 | **可达** | 同上(HTTP 活着);443 超时 |
| VM 内 :10432(local_proxy)/:9399(sql_exporter)/:25183(neonvmd)/:22(sshd) | 全活着 | 服务指纹确认 |
| :4432(local_proxy PG)/:6432(pgbouncer) | 需真凭据 | **仅 127.0.0.1:5432 是 trust**(认证配置不一致) |
| 10.0.0.1/10.96.0.1/10.96.0.10:5432 | 黑洞超时 | 网络策略 DROP |
| DNS 枚举 neon-control-plane ns | NXDOMAIN | safekeeper/pageserver 等不在该 ns |

**含义**: 租户 compute 的 postgres 后端进程能**直连 K8s 集群内部网络**(cluster.local DNS + 172.20.0.0/16 路由通)——SSRF 式横向起点。
**诚实边界**: dblink 仅 PG 协议(对 gRPC/HTTP 只能指纹不能发内容);内网无免密 PG 服务(无第二跳)——不构成 Critical,作为 High 链路的附加影响与修复输入(compute 出口网络策略缺失)。

## 9. 修复建议

1. **补丁语言盲区**: 拦截范围需覆盖 C 语言扩展函数(dblink 等),而非仅 plpgsql——或按函数属主+namespace 组合判定
2. **本地认证硬化**: 127.0.0.1:5432 改 scram(cloud_admin 设密码)或 local peer;pg_hba 禁用对 cloud_admin 的 trust
3. **平台表写保护升级**: neon_check_for_superuser() 触发器改为拒绝 cloud_admin(平台进程改用独立通道写)
4. **补丁扩展**: superuser 上下文拦截范围从"非 superuser 函数"扩展到"pg_catalog 高危内置函数白名单"(文件读写: pg_read_file/pg_read_binary_file/pg_ls_dir/lo_export/lo_import;信号: pg_terminate_backend;配置: pg_reload_conf 等)
5. **repack_trigger 改造**: 改为 SECURITY INVOKER 或对 SPI 语句剥离 definer 权限(SET search_path + current_user 恢复)
6. **函数权限硬化**: 对 cloud_admin 专属函数不授 PUBLIC EXECUTE;pg_catalog 敏感函数 REVOKE(与 PG 惯例冲突,需补丁层处理)
7. **文件系统隔离**: 平台配置(compute_ctl/local_proxy/pgbouncer)chmod root-only;PG 用户最小化文件权限
8. **扩展面收敛**: 评估 pg_repack/dblink 等扩展对租户的 trusted 放行策略
9. **compute 出口网络策略**: postgres 后端仅允许到 storage 层/neonauth 的必要流量,禁 cluster.local 全量 DNS 解析与 172.20.0.0/16 直连(经 NetworkPolicy/eBPF 层拦截,而非依赖 VM 内 iptables)

## 10. 脚本索引

| 脚本 | 内容 |
|---|---|
| _pg35_builtin_default.py | DEFAULT 载体 pg_read_file 首证 |
| _pg36_file_scope.py | 目录侦察 + environ(子查询限制失败记录) |
| _pg37_rule_exfil_fn.py | RULE 载体确认(pg_read_file/pg_ls_dir/bytea) |
| _pg38_conf_read.py | $PGDATA 配置读取 + /proc cmdline 全景 |
| _pg39_proxy_conf.py | local_proxy/pgbouncer 配置 + 端口探测 |
| _pg40_write_proof.py | lo 链初探(WHERE void 技巧失败) |
| _pg41_check_void.py | CHECK 载体 ACL 预检发现(DENIED) |
| _pg42_lo_export_wrap.py | 子查询包装 void 函数成功 |
| _pg43_lo_debug.py | 文件落点确认(/tmp + PGDATA, stat 17B) |
| _pg44_cleanup.py | 残留覆盖 0 字节 + DB 全清 |
| _pg45_grade_check.py | 定级验证(/etc/local_proxy 可写 + dblink 可装) |
| _pg46_dblink_probe.py | dblink 直连矩阵(防继承机制堵死) |
| _pg47_dblink_definer.py | **RULE 内 dblink 成功 → cloud_admin 连接(突破)** |
| _pg48_superuser_confirm.py | cloud_admin 身份/能力确认 |
| _pg49_platform_write.py | 平台表写实锤(IUD 全成功零残留) |
| _pg50_lateral_probe.py | **K8s 内网横向探测(control-plane-api/S3-gateway 可达实锤)** |
| _pg50_cleanup.py | 中断后残留清理确认(全清) |

**残留说明**: PGDATA/k_probe_x.txt、/tmp/k_probe_x.txt、/tmp/k_proof.txt、/tmp/k_proof_v8.txt 均为 0 字节空文件(无 unlink 函数可用),compute 重启自动清除;DB 侧 repack/public 全空、扩展已 DROP;lakebase 探测行已删(verify clean=0)。_pg50 中断残留(k_src/log_41746 等)已由 _pg50_cleanup 全清并复核([after] 仅 plpgsql/pg_session_jwt)。
