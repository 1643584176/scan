# HubSpot 项目状态：已搁置（2026-08-07）

## 结论
中国区无法完成 Persona vetting（身份验证），账号 96986967 会话全部失效，项目搁置。

## 关键信息存档
- 账号：base_pccp@protonmail.com（userId 96986967, emailId 232522058）
- portalId：247013359（已停用）、247013508（vetting 卡住）
- hublet：na2（api-na2.hubspot.com）
- cookie：hs_cookie_full.txt（na1 会话，已失效）

## 已确认的 HubSpot 规律
1. **signup 新账号注册** → 不触发 vetting ✅
2. **已登录账号创建附加 portal** → 触发 Persona vetting ❌（中国区过不了）
3. **引导不完成** → portal 被停用（myaccounts 无入口，API 403 deactivated）
4. **hubless 用户级 API**（login-verify/user-info、userpreferences/v1/profile）→ 不受 portal 状态影响，仅需 hubspotapi + csrf.app cookie
5. **hublet 隔离**：na1（app.hubspot.com）与 na2（app-na2.hubspot.com）cookie 不互通
6. **488 错误**："Hub X is unknown to this Hublet, but it appears to exist in Hublet Y" → 服务端指示正确 hublet
7. **401 priority invalidated** → 会话被风控失效（vetting 触发/异常模式）

## 已获得的用户信息
- user-info: id=96986967, firstName=base_pccp, verified=true, 141 个 enabledGates
- 敏感字段：canSelfDelete=true, scim=false, verificationSource=SIGNUP

## 恢复路径（如未来继续）
用 base_errort@protonmail.com 走 signup 注册全新账号 → 不创建附加 portal → 只测 hubless 用户级 API 面（profile/login-emails/user-info IDOR 方向）

## 未完成的测试方向
- PUT /api/userpreferences/v1/profile 的 userId 注入（IDOR 改他人资料）
- loginEmails/emailId 跨用户操作
- actingUserId 头探测（user-info 响应含 actingUserId 字段）
- myaccounts 列 portal API 的 IDOR
