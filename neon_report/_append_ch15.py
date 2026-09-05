# -*- coding: utf-8 -*-
"""append ch15 (V30 SQLi blind) to Neon auth report"""
p = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
ch = """

---

## 15. SQL 注入盲测：能否借注入查其他用户数据（V30, 2026-09-05）

> 触发：用户追问"SQL 注入可以吗，通过这个查其他用户数据"。对 auth API 业务字段与 console
> 参数执行时间盲注矩阵（pg_sleep 载荷，全部只读/无写入），并评估"即使注入成立是否可达他人数据"。

### 15.1 盲注矩阵结果

| 面 | 载荷 | 结果 | 判定 |
|---|---|---|---|
| auth sign-in email（13 载荷：引号/分号/注释/\|\|拼接/AND pg_sleep/UNION/子查询/大小写/dollar-quote/反斜杠/换行/tab） | 全部 | **400 INVALID_EMAIL**（Zod 邮箱格式校验先于 SQL） | 校验前置拦截，无注入面 |
| auth sign-up name（3 载荷） | `x'` / `x'\|`pg_sleep(3)\|`'` / AND 子查询 | **200 注册成功，name 原样入库，恒定 ~1s 无延迟** | 参数化查询（name=字符串字面量） |
| auth sign-up / reset-password email | 注入变体 | **400 VALIDATION_ERROR**（同 Zod 拦截） | 无面 |
| console branch name（3 载荷） | 引号/拼接/semicolon | **201 创建成功，name 原样，无延迟** | 参数化安全 |
| console role name/password | 引号/拼接/分号 | 404（路由路径差异，面已由 _e2 轮 role_names 取证闭合：payload 成字面量角色名） | 参数化安全 |
| Data API（PostgREST filter/select/order/limit/rpc） | _j13 矩阵（9 载荷） | 全部闭合（此前轮次） | 参数化安全 |
| auth 库名路由参数 | V23 轮 13 字符探针 | 全部 404/400（此前轮次） | 参数化安全 |

### 15.2 架构判定：即使注入成立也查不到"其他用户"

1. **auth API 的数据路径 = 本项目 DB**（pg_stat_activity 实锤：neon_auth role 实时写本项目 neondb 的 session 表）→ 注入 SQL 若成立，执行上下文 = 本项目库/neon_auth role → 只能操作本项目数据 → **跨租户不可能**
2. **console API（唯一中央控制面）**：branch/role 参数实测参数化安全 → 无注入 → 中央库不可达
3. **Data API**：PostgREST 参数化 + 连接本项目库 → 无跨项目
4. 数据按项目物理隔离（V29 已验证：实例内无他人库/角色/活动）→ **不存在"注入点→他人数据"的路径组合**

### 15.3 结论

**SQL 注入面不存在**（全部参数化 + Zod 校验前置），且架构上（auth/Data API 只连本项目库、console 参数化、数据物理隔离）
**不存在任何可通过注入触及其他项目/用户数据的路径 → 无洞**。V30 测试注册的 4 个临时用户已清理（users 复原 11）、
临时分支已删。
"""
with open(p, "a", encoding="utf-8") as f:
    f.write(ch)
print("appended, now %d lines" % len(open(p, encoding="utf-8").readlines()))
