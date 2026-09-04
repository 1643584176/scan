# Neon Auth 用户面双用户测试 (staging, 2026-09-03)

范围:neonauth host(ep-crimson-fog-w2gucld1.neonauth.us-east-2.aws.neon.build)better-auth 定制版
用户面 = Auth 服务内多用户隔离与 org 插件权限(非 console 控制面组织,因单账号限制无法做跨租户对照)

## 测试身份与通道
- 注册通道:`Origin: http://localhost:3000` 放行(project_config.allow_localhost=True),免邮箱验证
- 认证:cookie `__Secure-neon-auth.session_token=<token>.<sig>`(服务端签名);Bearer token 不被接受(401)
- 用户:na1 `+na1@gmail.com`(owner 视角)/ na2 `+na2@gmail.com`(member 视角)/ na3 `+na3@gmail.com`(第二 member 视角)
- project_config 关键项:email_and_password.enabled、requireEmailVerification=False、organization 插件 enabled
  (creatorRole=owner, org limit 10, membershipLimit 100)、social google/github isShared

## 端点面(全部存在)
org 插件:create/update/delete/leave/invite-member/accept-invitation/reject-invitation/cancel-invitation/
remove-member(memberIdOrEmail)/update-member-role(memberId+role)/list;set-active;check-slug 不存在
用户面:sign-up/email、sign-in/email、get-session、list-sessions、update-user、change-password、
revoke-sessions、revoke-other-sessions、verify-email(query token);forget-password/reset-password 未开放(404)
admin 插件未注册(impersonate-user 404,list-users 401)

## 测试矩阵与结果(全部防护正确)
| 测试点 | 结果 |
|---|---|
| 非成员 update/delete org | 400 USER_IS_NOT_A_MEMBER_OF_THE_ORGANIZATION |
| 非成员 invite-member | 403 YOU_ARE_NOT_ALLOWED_TO_INVITE |
| member 自提权 owner/admin | 403 YOU_ARE_NOT_ALLOWED_TO_UPDATE_THIS_MEMBER |
| member 降级/移除 owner | 400(only-owner leave 保护,无越权) |
| member delete org | 403 |
| member leave 后旧 cookie | list 空/update 400,权限即刻失效 |
| 跨 org 操作(org1 member 操作 org2) | 400 USER_IS_NOT_A_MEMBER |
| 邀请绑定(ghost 邮箱邀请被他人接受) | 403 YOU_ARE_NOT_THE_RECIPIENT_OF_THE_INVITATION |
| 正常邀请→接受 | 200,role 取邀请固定值(不可客户端篡改) |
| sign-up 注入 role/banned/emailVerified | 400 FIELD_NOT_ALLOWED |
| update-user 改 email(含占用/新址) | 400 EMAIL_CAN_NOT_BE_UPDATED(email 完全锁死) |
| update-user 注入 role | 400 FIELD_NOT_ALLOWED |
| 重复 sign-up | 422 USER_ALREADY_EXISTS |
| slug 冲突创建 | 400 ORGANIZATION_ALREADY_EXISTS |
| cancel-invitation(owner 撤销) | 200 status=canceled |

## 安全观察
1. neon 定制明显针对 better-auth 上游缺陷做了加固:email 更新关闭(上游默认允许)、字段白名单校验
   (FIELD_NOT_ALLOWED 为定制错误)、邀请 email 归属校验(GHSA-fmh4 org invitation ownership 修复在位)
2. remove-member 对 owner 目标走 leave 语义并受 only-owner 保护(响应信息未区分操作者,仅语义细节)
3. session cookie 签名完整(token.sig),Bearer 模式完全禁用(减少 token 泄露面)
4. admin/impersonation 未注册;forget-password 未开放(攻击面收敛)

## 结论
neon_auth 用户面(单租户内多用户隔离 + org 权限 + 邀请流)全部防护正确,无越权/提权/绑定缺陷。
GHSA-g38m(OAuth account linking)/GHSA-fmh4(org invitation)对照:未发现可复现点(social 登录需真实 Google
授权,未能全链验证;若需继续需用户提供 OAuth 回调配合)。
本轮注册测试用户 na1/na2/na3 保留于 neon_auth.user,org/member/invitation 已全部清理。
