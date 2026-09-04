# -*- coding: utf-8 -*-
# _app_round4.py - append round-4 (Identity management surface) conclusions to progress md
import io

ADD = """
## 轮次4: Netlify Identity 管理面挖掘 (2026-09-02)

### 决策
用户选择方向1(Identity 管理面)。Identity 不在导出 OpenAPI 内,是独立微服务面。

### 面图景(三层架构)
1. **api.netlify.com /api/v1/sites/{sid}/identity/{iid}/... 管理面**(swagger 外影子面):
   - POST /sites/{sid}/identity 空 body=启用 identity → 201 instance(id=6a97f260e3e0091b16d132ce, url=identity.services.netlify.com, config 含 site_url/smtp/mailer/external/disable_signup/webhook/cookies);重复 422 "already installed"
   - GET /identity/{iid} → 完整 instance+config;GET /users → 裸数组;GET/PUT/DELETE /users/{uid};POST /users 201;POST /users/invite 204
   - 本质=薄包装层转发 GoTrue(错误内层 GoTrue 格式如 "Bad Pagination Parameters: strconv.ParseUint" 外包 {"error":...})
   - **字段白名单**:PUT/POST 只透传 user_metadata/app_metadata;password/email_confirm/confirmed_at/role/aud/ban_duration/confirmation_token/recovery_token 全被过滤(创建用户无密码,登录报 password invalid 而非 Email not confirmed)
   - PATCH/PUT instance config 204 但恒不生效(stub;与 2020 论坛帖 "PUT identity/{id} 204 not working" 一致)
   - **authz 正确**:TOKEN_B 打 A 的 instance 全部 404(site_id URL 参数纯装饰,鉴权走 instance→site 关联)
2. **site 域名 {name}.netlify.app/.netlify/identity/... GoTrue 单实例**(启用后生效):
   - 公开面活:POST /signup(200,disable_signup=false 默认开放+邮件确认 autoconfirm=false)、/token(password grant **必须 urlencoded**;JSON body 报 unsupported_grant_type!)、/recover 200{}、/logout POST
   - POST /token 未确认用户 → invalid_grant;管理面用户无密码 → 恒 password invalid
   - /admin /admin/settings 到 GoTrue(401 Bearer);/admin/users 等被 CDN 精确挡(404 HTML)
3. **identity.services.netlify.com 共享 GoTrue**(/health 200 显示 GoTrue+version hash 6d9da840):
   - 多实例 operator 模式:/settings /admin/* 需 **x-nf-sign 头**(HS256 JWS,共享 OperatorToken 签,claims={id=instance_uuid, netlify_id, site_url, function_hooks});伪造 → "signature is invalid";无 → 400 "Operator microservice headers missing"
   - /instances 需 Authorization Bearer==OperatorToken(SecureCompare;猜测 operator/netlify/foobar 全 401)

### 源码审计(netlify/gotrue 开源 fork,浅克隆到 _gotrue_src)
- requireAdminCredentials: Bearer==OperatorToken 直接 admin;否则 JWT HS256 严格验签(alg=none 拒)+DB 查 user(IsSuperAdmin 或 role==AdminGroupName "admin",**role 列非 app_metadata**)
- JWT claims 无 role;kid=nf-ident;sub=user UUID 或 SystemUserUUID
- filter 参数化 LIKE;sort 白名单 created_at;referrer 必须同 hostname;token 熵 SecureToken;signup 只收 user_metadata
- 未确认用户不可 password grant("Email not confirmed")

### 发现(候选,均不达 H1)
1. **CDN 白名单绕过(双斜杠/./..)**:/.netlify//identity/settings 200、/admin/users 401 到 GoTrue(正规路径 404 HTML);但 settings 仅公开配置(external 开关/disable_signup/autoconfirm,与源码一致无敏感),admin 仍需 admin JWT → 无实际影响
2. GET/PUT/DELETE /users/invite → 500(路由把 invite 当 user_id,内部错误 "user_id must be an UUID",应 400/404)
3. 分页参数非法(per_page=-1/page=abc)→ 500 包裹(应 400)
4. POST /users/invite 对不存在用户 204 空操作(GoTrue invite 需用户存在,错误被吞;对存在用户也无 confirmation_sent_at 变化)
5. 管理面 POST /users 201 响应无确认状态字段(email_confirm 被过滤且无提示)

### 结论
跨账号隔离/AuthZ/JWT/operator 全正确。GoTrue fork 无通用洞(生产 commit 6d9da840 与 master aac5b573 接近)。**无可提交洞**。

### 清理
4 测试用户 DELETE 204;instance DELETE 204(site identity_instance_id 回 null,恢复原状;可复现:POST /sites/{sid}/identity 重新启用)

### 教训
- api.netlify.com 上无 token 401 ≠ 路由活(全局鉴权先行);带 token 后文本 404=死、JSON 404=活(应用层)
- identity 管理面在 swagger 外,只能靠论坛帖子/黑盒探活发现启用入口(POST /sites/{id}/identity)
- GoTrue /token 只认 urlencoded(body JSON 会 unsupported_grant_type 误导)
- 管理面"204 无 body"未必生效(PATCH stub 与字段过滤),必须 GET 回读验证
- 生产 GoTrue 版本可通过 /health version hash 与开源仓库对比
"""

path = r'D:\scan\netlify_report\progress-2026-09-02.md'
with io.open(path, 'a', encoding='utf-8') as f:
    f.write(ADD)
print('appended, new size:', __import__('os').path.getsize(path))
