# -*- coding: utf-8 -*-
"""append ch13 (V27-V28 user-table deep dive) to Neon auth report"""
p = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
ch = """

---

## 13. 用户表思路深挖：neon_auth user/session/account/verification 全量审计（V27-V28, 2026-09-05）

> 触发：用户提示"他们有用户表吗，思路打开"。此前追 jwks 私钥链断于信封加密即止步，
> 但 user/session/account/verification 四张表是**活数据**（登录态/凭证/密码哈希），才是真正的面。
> 本轮全量 dump + DB→API 能力链验证。

### 13.1 四表全量 dump 结论

| 表 | 行数 | 内容 | 关键发现 |
|---|---|---|---|
| user | 11 | id/name/email/emailVerified/role/banned/banReason/banExpires/image/时间戳 | **11 行全部为本项目测试账号**（libobo1229+na1/na2/na3/secn12/na_w1/na_org1/2/3/v5frxh/v5bxvgo/v65hxc），**无任何外来/跨租户用户**；emailVerified 全 False、role 全 user |
| session | 154 | id/token/ipAddress/userAgent/userId/**impersonatedBy**/activeOrganizationId/过期时间 | **token 明文存储**（32 字符随机串）；token = 纯会话串，**与 Set-Cookie 值不等价**（cookie 附加 HMAC 签名段）；含 impersonatedBy 列（admin 冒充功能存在）；activeOrganizationId 列（会话级活跃 org） |
| account | 11 | providerId/accountId/userId/accessToken/refreshToken/idToken/scope/**password** | providerId=credential 的行 password = **scrypt salt:hash**（32hex salt : 64hex hash）；OAuth 行 token 列为 NULL（未存第三方 token） |
| verification | 14 | identifier/value/expiresAt | **OAuth PKCE 流程残留**：codeVerifier/nonce/state(b64+HMAC) 明文落表（9/4 已过期）；**email-verification-otp** 条目（value=base64 hash:0）；**reset-password** 条目（identifier=随机 token，value=userId，10 分钟窗口） |

### 13.2 DB token → API 冒充验证：**cookie HMAC 签名阻断（安全设计）**

- sign-in 响应 Set-Cookie = `__Secure-neon-auth.session_token=<token>.<b64签名>`（签名 = cookies.secret 派生 HMAC）
- **DB session 表只存 token 前半**（无签名段）→ 用 DB 偷来的 token 直调 API：get-session 200-null、org/list 401 UNAUTHORIZED
- 文档佐证：官方 SDK 代码 `cookies: { secret: process.env.NEON_AUTH_COOKIE_SECRET! }`（neon.com/docs/auth/overview）→ **DB 泄露（含 session 表全量）≠ 可冒充**，纵深防护到位（positive finding）

### 13.3 owner DB 写能力矩阵（全部验证，全部恢复）

| 操作 | API 效果 | 验证 |
|---|---|---|
| UPDATE user.role='admin' | admin/impersonate-user 200（拿到任意用户 session！）、ban-user 200 | V28c：role 改 admin → 登录 → impersonate-user U2 成功 → role 恢复 user |
| UPDATE account.password（复制已知 hash） | **完整接管**：用 U1 密码登录 U2 成功（200 完整 session），恢复原 hash 后 U2 原密码登录正常 | V28d：hash swap 全流程 |
| INSERT organization+member(owner) | API 立即可见/可操作（invite-member 可用） | V28b：DB 造 org → U1 org/list 可见 → 清理 |
| INSERT session 行 | 无效（缺 cookie 签名） | V28：DB 直插无意义 |
| 低权限 role（V26 已证） | 读 SELECT 全 DENY；写 INSERT/UPDATE 同 DENY（表权限仅授 owner/服务 role） | V26 权限矩阵 |

### 13.4 信任模型判定：**全部落在官方声明能力内 → 无洞**

Neon 官方文档（neon.com/docs/auth/overview，2026 现行版）原文：

> "It stores users, sessions, and auth configuration directly in your Neon database."
> "**Identity lives in your database** — All authentication data is stored in the neon_auth schema. **It's queryable with SQL** and compatible with Row Level Security (RLS) policies."
> "Use Managed Better Auth as the identity system for your app. Store users, sessions, and OAuth configuration directly in Postgres, and pair with RLS for secure, database-centric access control."

→ **"queryable with SQL" + "pair with RLS"** 即为 Neon 声明的信任模型：
1. 项目 owner 对 neon_auth 全量数据（用户/会话/密码哈希）拥有读写权 = **产品特性**（数据主权，分支/迁移/SQL 管理场景依赖此设计）
2. 数据保护责任 = **用户自配 RLS**（文档推荐做法），平台不做隐藏
3. 平台侧实际防护：表权限仅授 owner/服务 role → 低权限 DB role 全 DENY（已验证）；cookie HMAC 签名密钥在服务端 → 表内 token 无法直接冒充（已验证）

### 13.5 补充观察（Informational，留档）

- **admin/impersonate-user 端点存在**（匿名 401、普通用户 403 YOU_ARE_NOT_ALLOWED_TO_IMPERSONATE_USERS、DB role=admin 后 200）——管理冒充面仅 owner 可达，规则内闭环
- verification 表 OAuth 流程残留 codeVerifier/nonce 明文 + reset-password token 明文——仅 owner 可读（设计内），且均有时效窗口
- user.role/banned 直改即时生效于 API 层（无独立鉴权缓存）——对 owner 是便利，若未来开放"部分权限 DB role"需警惕（当前表权限全 DENY 无此风险）
- session.impersonatedBy 列佐证 impersonation 功能实现存在

### 13.6 判定

**无安全后果。** 用户表全链（读 4 表、改 role、改密码 hash、插 org/member）均落在 Neon Auth 官方声明的 "identity lives in your database, queryable with SQL, pair with RLS" 模型内；平台纵深（表权限仅授 owner + cookie 签名）已实测有效。低权限 DB role 对 neon_auth 全表读写双 DENY → 无低权限提权面。环境零残留（V28b 临时 org/member 已删、U1 role 与 U2 hash/ban 状态全部恢复原值）。
"""
with open(p, "a", encoding="utf-8") as f:
    f.write(ch)
print("appended, now %d lines" % len(open(p, encoding="utf-8").readlines()))
