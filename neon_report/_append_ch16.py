# -*- coding: utf-8 -*-
"""append chapter 16 (V31-V38 recon close) to Neon auth report"""
ch = """

## 第 16 章 剩余攻击面侦察闭合(V31-V38,2026-09-05)

> 触发:用户问"还有什么地方可以"。对 9/4 闭合报告点名的未测面(Buckets/Functions/Auth webhooks)与
> console 管理面做系统侦察,并全量枚举 auth 路由,全部闭合。

### 16.1 Beta 功能面侦察(V31):stage 未开放

| 面 | 探测 | 结果 |
|---|---|---|
| Buckets(对象存储 Beta) | GET projects/{p}/buckets 等 4 路径 | 全 404(route does not exist) |
| Functions(Beta) | projects/{p}/functions | 404 |
| console auth 配置端点 | /auth /auth/config /auth/providers /auth/jwks 等 9 路径 + POST | 全 404 |
| branch 级 auth 端点 | branches/{br}/auth | 404 |
| webhook 启用面 | webhook_config = {'enabled': False, 'enabledEvents': [], 'timeoutSeconds': 5} | **无 URL 字段、无 console 启用路径、事件无外发目标** → 无 SSRF 载体 |

### 16.2 Data API 函数面(V31b):无平台函数暴露

- /neondb/rest/v1/rpc/{任意函数名} → 404 PGRST205(schema cache 无此函数)
- public schema 内除 plpgsql 无任何可调函数(查询 pg_proc: public/neon_auth 无 PUBLIC EXECUTE 函数)
- → PostgREST rpc 面不存在可利用对象(平台函数不暴露给租户 Data API)

### 16.3 project_config 全字段穷尽(V31b/c)

- 12 列全 dump:trusted_origins=[](空)、social_providers=google/github(isShared=True,无自定义 issuer)、
  email_provider=shared、email_and_password(emailVerificationMethod=otp, requireEmailVerification=False,
  sendVerificationEmailOnSignUp/OnSignIn=False)、allow_localhost=True
- plugin_configs 全 JSON:magicLink(disabled)/phoneNumber(disabled)/organization(enabled, creatorRole=owner,
  membershipLimit=100, organizationLimit=10, sendInvitationEmail=False)——**无任何 secret/私钥/URL 字段**
- → 配置面穷尽(唯一写路径=owner 直写 DB,已证明设计内)

### 16.4 console 管理端点枚举(V32):25+ 猜测全 404

api_keys/members/invites/organizations/consumption/settings/audit/billing/plans/webhooks/notifications +
project 级 archive/operations/members/api_keys/usage/audit/ip_allow/network_restrictions/databases/snis/
custom_hostnames/compute + branch 级 backups/data/schema/inspect/auth/roles/api_keys → **全 404 HTML**
→ stage console API 面收敛,仅 V 系列已测端点集(V32 后无新 console 管理端点)

### 16.5 前端 JS 端点提取(V33-34):本地 _js 为生产 Databricks 前端

- neon_report/_js(app.js + prod_chunks)标记检查:databricks 18 处、无任何 stage 标记
  (console-stage/I-LOVE-PREVIEWS/staging-realm)→ 该抓包是**生产** Databricks 化 console,与 stage 不一致,弃用
- stage / → 302 Keycloak(HTML 面需 cookie 会话,无 manifest)
- → 前端端点提取路线关闭(stage 前端不匿名可达)

### 16.6 auth 路由全枚举(V35):80 标准路由 × GET+POST → 37 存在

新发现 8 端点(对照 V15 矩阵):**refresh-token / change-email / change-password / list-sessions /
revoke-session / revoke-other-sessions / list-accounts / admin/set-user-password** + 确认 verify-email
GET 活着(修正 V 时代"verify-email 缺失"记录——端点存在,此前方法/路径误判)

### 16.7 新端点语义验证(V36-37):全部设计内,无洞

| 端点 | 实测 | 判定 |
|---|---|---|
| refresh-token | 需 providerId;google→ACCOUNT_NOT_FOUND(U1 无 OAuth 链接);credential/email→PROVIDER_NOT_SUPPORTED | OAuth token 刷新,self 语义 |
| change-email | CHANGE_EMAIL_DISABLED | 功能关闭 |
| change-password | 需 currentPassword(标准) | 设计内 |
| list-sessions | 200 返回 self 会话含 token 明文 | self 会话管理(与 DB session 表一致) |
| list-accounts | 200 self 账号列表 | self |
| revoke-* | 401/需 body | 标准 |
| verify-email 闭环 | **request-email-verification→404;sign-up 不生成 OTP 记录**(sendVerificationEmailOnSignUp=False);V36 所见 2 行 OTP 为 13:37 历史残留(已删) | **验证触发链不存在** → email 验证面功能封闭 |
| callback/google | 无 state → 302 error?state_not_found | 标准 state 校验 |

### 16.8 结论

**Neon Auth/Data API/console-stage 可测面已穷尽**(五轮矩阵 + 本侦察 7 项系统排除 + 80 路由全枚举)。
无可提交候选。剩余方向需新资源:① OAuth 真实账号完整流程(redirect_uri/state 变体,需 google 交互);
② 分支 auth 隔离(需重建分支 endpoint);③ 生产面(规则要求邮件协调);④ 第二 console 账号(成员/邀请跨主体)。
环境零新增残留(users 复原 11,sessions 120 含本人活跃登录,verification 13=既有 OAuth 测试数据,OTP 类全清)。
"""
p = r"F:\scan\neon_report\Neon-Auth与DataAPI技术面-20260904.md"
with open(p, "a", encoding="utf-8") as f:
    f.write(ch)
print("appended", len(ch), "chars")
