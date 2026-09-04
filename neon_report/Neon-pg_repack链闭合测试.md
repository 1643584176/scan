# Neon pg_repack / cloud_admin 提权链闭合测试归档

- 日期:2026-09-03
- 环境:Neon staging 直连 PG(ep-crimson-fog-w2gucld1)
- 对照:Netlify pg_repack 提权链(已提交,根因在 Neon 侧 repack schema ACL + definer)
- 结论:**链在 Neon 被双层防御封死(负结果,证据完整)**

## 1. 攻击面前提(全部实测成立)

| 前提 | 实测 |
|---|---|
| 用户可 CREATE EXTENSION pg_repack 1.5.2 | OK(对象 owner 均为 cloud_admin) |
| repack.repack_trigger = SECURITY DEFINER as cloud_admin | OK |
| cloud_admin 为真 superuser(rolsuper=True,可读 pg_authid/建角色) | OK |
| 用户经 neon_superuser 成员可 CREATE 于 repack schema | OK |
| 用户不可 SET ROLE cloud_admin(非其成员) | DENIED(链必要性成立) |

## 2. 攻击机制(Netlify 同构)

用户自建表 k_src + AFTER INSERT 触发器 `repack.repack_trigger('id')`:
- 用户 INSERT k_src → repack_trigger 以 **cloud_admin** 身份 SPI 执行
- SPI 内 `INSERT INTO repack.log_<oid>` → 触发 log 表上的用户可控对象
  (触发器函数 / CHECK 约束 / column DEFAULT / RULE 动作 / 复合类型)

## 3. 补丁拦截矩阵

| 路径 | 结果 | 错误 |
|---|---|---|
| [A] CHECK 约束函数 | 拦 | Invocation of non-superuser function by superuser |
| [C] RULE + plpgsql 函数 | 拦 | 同上 |
| [D] BEFORE/AFTER 触发器函数 | 拦 | 同上 |
| [E] column DEFAULT 函数 | 拦 | 同上 |
| [B] RULE 纯 DML | **放行但无提权**(见 4) | — |

补丁机制:superuser(cloud_admin definer SPI)上下文调用**非 superuser 属主函数**即拒绝,
覆盖面含触发器/约束/DEFAULT/RULE 内函数调用,与语言无关(plpgsql 均测)。

## 4. RULE 纯 DML 残留面分析(关键)

假设:规则动作以执行者(cloud_admin)身份执行 → 可写 pg_authid 等平台对象。
实测否定:

- RULE 动作 `SELECT rolname, rolpassword FROM pg_authid → k_exfil`:成功
  **但用户直读 pg_authid 本就成功**(见 5),无增量
- RULE 动作 `UPDATE pg_authid SET rolconnlimit=rolconnlimit WHERE rolname='neondb_owner'`
  (no-op 零破坏):**DENIED permission denied for table pg_authid**
  → PG 规则系统表权限按**规则属主(用户)**检查,不随执行者(cloud_admin)提升
- CREATE RULE 引用无权限表不报错(执行期检查),不可作为探测信号

结论:双层防御 = Neon 函数调用补丁(拦执行层) + PG 规则 owner 权限模型(拦表层)。
RULE 纯 DML 仅能以用户自身权限写用户有权的对象 → 无攻击价值。

## 5. 旁路发现(环境配置,非漏洞)

- neondb_owner 成员链:→ neon_superuser → pg_read_all_data / pg_write_all_data / pg_maintain / pg_monitor 等
- 因此用户**可读 pg_authid(26 行,其中 4 行含 scram 哈希)**,可读写 neon_auth schema 全部表
  ——Neon 单租户设计(用户即自己 DB 的数据 owner),与 Netlify 多租户隔离模型不同,不构成跨租户面
- pg_shadow/pg_roles/pg_stat_ssl 均可读;pg_user_mappings 0 行

## 6. 残留

- 注入测试遗留角色 `x"; CREATE ROLE pwn LOGIN; --`(rolsuper=False,无 LOGIN)
  DROP 被拒(无 ADMIN OPTION)——无害,留待平台清理;若需上报可提及
- 所有 k_* 测试对象/扩展已清理(终验:public/repack 0 表,pg_repack 卸载,k_* 函数 0)

## 7. 测试脚本索引

- _pg8_ext_audit.py 扩展面 + 全库 SECURITY DEFINER 枚举(空)
- _pg9_repack_probe.py CREATE EXTENSION + owner 审计(链前提)
- _pg10_roles.py 角色属性 + 成员链
- _pg11~_pg13 PoC v1/v2(定位补丁阻断点)
- _pg14_patch_boundary.py 补丁矩阵 A/B/D
- _pg15_rule_fn.py RULE+函数/C2 与 DEFAULT/E 复查(清理段曾漏 log2 表→已修)
- _pg16_fix_cleanup.py / _pg17_final_clean.py 残留清理与终验
- _pg18_rule_exfil.py RULE 读 pg_authid(发现直读基线)
- _pg19_perm_model.py ACL/成员/列级可读性
- _pg20_member_chain.py 递归成员链 + SET ROLE + pwn 残留
- _pg21_rule_update.py RULE no-op UPDATE pg_authid(决定性负结果)

## 8. 结论

Neon 对 pg_repack definer 链做了**系统性加固**(函数调用补丁),配合 PG 规则 owner 模型,
Netlify 同构链在 Neon 不可复现。该面闭合。
