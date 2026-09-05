# Neon Auth / Data API 技术面测试（2026-09-04）

> 阶段：续 #3992341 之后的技术层（非业务）漏洞挖掘
> 目标：ep-crimson-fog-w2gucld1（A=orange-sun-90493739）+ 新建临时项目 B（broad-violet-25805528，测完已删）
> 合规：X-Bug-Bounty: xxbo；零破坏（即建即清/同密码变更/配置恢复）；测试账户 libobo1229+na2/nb1(已随项目删)

## 1. Auth 会话与 CSRF 面（_j14~_j19）

### Cookie 属性（全端点一致）
- `__Secure-neon-auth.session_token`：`Max-Age=604800; Path=/; HttpOnly; Secure; SameSite=None; Partitioned`
- sign-in/update-user/sign-out 重发均带 Partitioned（无去 Partitioned 化漏洞）；sign-out 清 3 个 cookie

### Origin 校验矩阵（POST 状态变更端点）
- 校验严格白名单：`http://localhost:3000` 通过；evil.com / null / 无 Origin / console-stage.neon.build / neon.build 子域 / 127.0.0.1 全拒（403 INVALID_ORIGIN 或 MISSING_OR_NULL_ORIGIN）
- 变体绕过矩阵（17 种）：校验=URL 解析后 host 匹配（localhost 任意端口/scheme/大小写/userinfo 均放行；子域/尾点/IP 拒绝）——**浏览器无法伪造 Origin，变体远程不可利用**，闭合
- 双 Origin header → 400（畸形请求，浏览器不可发）
- 端点清单 × evil Origin 全扫：sign-out/update-user/change-password/change-email/revoke-sessions/revoke-other-sessions/reset-password/send-verification-email/link-social/unlink-account/delete-user 全部 403 ✓
- 未启用路由（404）：forget-password/verify-email/request-email-change/update-email/two-factor/mfa

### ★ 发现：CORS 全反射 + GET 敏感端点无 Origin 校验（Low~Medium 候选）
- **OPTIONS 预检对任意 Origin 204 + ACAO 反射 + Access-Control-Allow-Credentials: true**（含 evil.com/null）
- **GET /neondb/auth/token**：无 Origin 校验（evil origin 200）+ 响应 `ACAO: https://evil.com` + creds:true → 返回 15min EdDSA JWT（role=authenticated，可调 Data API）
- **GET /neondb/auth/get-session**：无 Origin 校验 + ACAO 全反射 → 返回完整 session JSON（session id/ipAddress/userAgent/userId/expiresAt/createdAt）
- 对比：GET /list-sessions 有 Origin 校验（evil 401）——端点间不一致；POST 全有校验
- 防线分析：唯一防线 = cookie `Partitioned`（CHIPS）。无 CHIPS 浏览器（Chrome<114 / Firefox<137 / 旧 Safari / 企业浏览器）+ 允许第三方 cookie → evil 页面 `fetch(credentials:'include')` 可读 JWT 与会话元数据
- 影响验证：泄露的 session id（32 字符，无 HMAC 签名）**不能冒充**（伪造 cookie → 401 Unauthorized）；JWT 泄露可在 15min 窗口内调 Data API（authenticated 权限）；POST 状态变更仍被 Origin 校验挡（cookie 带了也做不了）
- 根因判断：Neon Auth 是跨域 API（任意客户 app 域 SDK 调用）→ ACAO 反射为功能必需；但 token/get-session 属"无需认证"路由组，漏了 Origin 校验，且与 CORS 中间件配置脱节
- 修复建议：非白名单 Origin 不反射 ACAO；或敏感 GET 端点加 Origin 校验（与 list-sessions 对齐）
- 评级评估：受浏览器特性限制，实际可利用人群 = 无 CHIPS + 允许第三方 cookie 的旧浏览器（2026 年主流已覆盖 CHIPS）→ **Low ~ Medium 边缘**，作为报告候选

### Mass assignment / 管理面
- sign-up/update-user 字段白名单：role/emailVerified/email/phoneNumber → `400 FIELD_NOT_ALLOWED` ✓
- admin 端点存在但 admin key 无弱默认（401）✓；api-key 端点不存在（404）✓
- redirectTo/redirect 参数：sign-in/email、sign-out GET → 404 无反射；error → 302 本地 `/?error=UNKNOWN` ✓ 无开放重定向
- .well-known 仅 jwks.json ✓

## 2. 跨租户 JWT 复用（_k1~_k3）——闭合

实测链：API key 建新项目 B → `POST /branches/{bid}/auth {auth_provider:better_auth}` → `POST data-api/neondb {auth_provider:neon_auth, add_default_grants:true}` → B 建表+授权 → A JWT 打 B：

| 请求 | 结果 |
|---|---|
| A(orange-sun) JWT → B Data API | 400 `jwk not found`（B JWKS 无 A kid）|
| B JWT → A Data API | 400 `jwk not found` |
| B JWT → B Data API（对照）| 200 正常读数据 |

- JWKS kid 项目级唯一：A=6ab964bf…、B=5ad782c0…；EdDSA/Ed25519 单 key
- **租户隔离正确，闭合**。无全局共享签名密钥

## 3. Role claim 耦合（_k4）——闭合

- 控制面 `PUT /branches/{bid}/auth/users/{uid}/role` 支持 custom role（含 neondb_owner，200 生效于目录）
- 但重新签发的 JWT **role claim 仍硬编码 `authenticated`** → 与 Data API `SET ROLE` 完全解耦 → 无提权注入面
- neon_auth 表清单：user/session/account/verification/organization/member/invitation/**jwks**/project_config（owner 直连可见，Data API authenticated 全 403）

## 4. 残留与清理
- B 项目已 DELETE（200）；nb1 测试用户随项目删除
- A 项目：db_schemas=['public'] 已恢复；测试表全部 DROP；na2 用户 role 已恢复 user
- 历史项目 damp-term-63384673 存在（非本次创建，未动）

## 5. 结论
- 技术层候选报告 1 个：**Auth CORS/凭证隔离面**（见 §1 ★）——依赖 CHIPS 浏览器特性，评级 Low~Medium 边缘
- 其余技术面（跨租户 JWT/role 耦合/mass assignment/CSRF/Origin 变体/注入矩阵/alg 混淆/schema 隔离）全部闭合

---

## 6. 补充面（同日二次扫描 _m1~_m6）——闭合

### 6.1 配置画像（控制面 GET /branches/{bid}/auth/*，首次读取）
- plugins：organization 开（limit 10 / member 100 / creator_role=owner / send_invitation_email=false）；magic-link 关；phone-number 关
- email_and_password：开；email_verification_method=**otp**；require_email_verification=false；disable_sign_up=false
- oauth_providers：google+github（type=**shared**——Neon 托管客户端）；allow_localhost=true；domains 白名单=[]（空）
- email_provider=shared（auth@mail.myneon.app）；webhooks 关
- auth/config GET 405（仅 PATCH）；plugins/organization|magic-link GET 405（仅 PATCH）

### 6.2 渲染/XSS 面——闭合
- 全 JSON：/ 404 JSON；error 参数 302 到 `/?error=UNKNOWN`（值被规范化，不反射）；404 页 text/plain 空 body
- 无 HTML 端点 → 无 neonauth 域 XSS 面

### 6.3 Legacy auth 端点（sunset 2026-03-01 应删未删，6 个月后仍全活）
- 路径：POST /projects/auth/{user,keys,transfer_ownership}（**无 project_id 路径参数，项目在 body**）；GET/POST /projects/{pid}/auth/{domains,email_server,users} 等
- auth_provider 枚举：mock/stack/better_auth（**不是 neon_auth**——legacy 接受 better_auth）
- **归属校验存在**：body 项目非本项目/无集成 → 404 project not found / no integration found；keys 返回 pub/secret 全空（better_auth 无 SDK key）→ 无跨项目越权
- 功能等价 branch 级端点（201 建用户 + legacy DELETE 204 清理成功）
- **副作用发现**：POST transfer_ownership → 200 {"url":""}，把 auth 集成 `transfer_status` 置 **initiated**（枚举仅 initiated/finished，无 cancel 端点、url 空无法完成）→ **半状态残留**（功能无损：sign-in/token/get-session 全部正常）——A 项目当前残留此状态，记录备查

### 6.4 OAuth 流程（google/github shared）——防护到位
- POST /neondb/auth/sign-in/social：redirectTo/callbackURL 校验存在（evil → 403 INVALID_REDIRECTTO/INVALID_CALLBACKURL）；localhost:3000 通过
- 成功返回两段式 init：`/sign-in/social/init?token=<uuid>`（DB verification 存储；无 cookie 绑定；可重放；无效 uuid → 400 VERIFICATION_NOT_FOUND）
- GET init → 302 Google：client_id=8734340308-psl9t4dj…（Neon 共享）；**redirect_uri=父域共享网关** `neonauth.us-east-2.aws.neon.build/auth/oauth/callback/google`；state=base64 JSON {"endpointId","database","providerName","timestamp"} + SHA256 HMAC；PKCE S256；scope=email+profile+openid
- state 无 redirectTo 字段（redirectTo 仅 POST 阶段校验+存储）；init 参数覆盖无效（redirectTo/provider/state 追加均不影响）
- 网关（父域）：直接访问无 state → 400 State not found AUTH_FAILURE；伪造 state/他人 endpointId + 假 code → 404/400（先验 state）
- 项目域 /neondb/auth/callback/{provider}：302 state_not_found/state_mismatch（better-auth 内部路径，与网关并行但非实际 redirect_uri）
- POST /neondb/auth/token → 404（无 OAuth token 端点）
- **结论：state 签名 + PKCE + 固定 redirect_uri + redirectTo 白名单齐全——OAuth 面无现代浏览器可利用点**

### 6.5 小发现（Informational，均不报）
- init?token 非 uuid 格式 → 500 泄露 PG 错误（`invalid input syntax for type uuid` 22P02, DATABASE_ERROR）——输入校验缺失 + 500
- transfer_status 半状态污染（见 6.3）

### 6.6 本轮最终结论
- **无现代浏览器可直接打的独立新洞**；CORS/凭证隔离面（§1 ★）仍为唯一报告候选
- 环境残留：A 项目 auth transfer_status=initiated（无 cancel 路径，功能无损，记录备查）

---

## 7. 控制面技术面 sweep（_m7~_m8l）——闭合

### 7.1 Beta 面全景（OpenAPI tags 统计）
- 未测类别：AI Gateway(1)/Consumption(3)/Logs(3)/Snapshot(7)/Storage(1)/Credentials(5 端点)
- Credentials 面为**新发现重要面**（S3+AI 共用 Neon bearer credential 系统）

### 7.2 ★ AI Gateway + Object Storage：真实存在但入口 WAF 封锁
- GET /branches/{bid}/ai_gateway → `{"enabled":true, "base_url":"https://br-wandering-field-w2ob6mpn-api.ai.c-1.us-east-2.aws.neon.build"}`（公网 IP 3.19.192.84）
- GET /branches/{bid}/storage → `{"enabled":true, "s3_endpoint":"...storage.c-1...", "region":"us-east-2", "force_path_style":true}`（公网 IP 16.58.106.110）
- **入口全 403（nginx 页，非应用错误）**：无 auth / 任意路径（/v1/models、/ai-gateway/openai/v1/*、/v1/chat/completions…）/ 有效 Bearer（nt_live_…）/ 无效 token 全部相同 403；S3 带有效 SigV4（boto3, us-east-2 + us-east-1 双 region）也 403 空 body → **WAF 层对 staging 数据面全封锁，外部黑盒不可达**
- 文档确认（neon.com AI Gateway auth）：正确路径 = base+/v1（chat）、+/openai/v1（Responses）、+/anthropic、+/gemini；模型列表仅 GET /v1/models；凭据 branch 绑定 + lineage 继承（main 凭据适用于其子分支）

### 7.3 Credentials 端点（控制面全通，无越权）
- POST /credentials：201 → token_id=nak_live_<32hex>（兼 S3 access key id）+ api_token=nt_live_<12hex>_<sec>（Bearer）+ s3_secret_access_key=nsk_live_<64hex>；scopes 枚举：storage:read/storage:write/ai_gateway:invoke/functions:invoke（授予集含 telemetry:write 内部 scope）
- reveal/rotate/revoke 全 204/200；平台自动存在默认凭据（"Default AI gateway credential" ai_gateway:invoke + "Default object storage credential" storage:read+write）
- schema 注释：reveal 按 (project_id, token_id) 定位不验证 branch（list 是 branch 级 → 仍需项目权限 → 无越权路径）
- 签发凭据全部 revoke 清理 ✓（默认凭据未动）

### 7.4 Logs 面（LogQL 子集，label 白名单）
- POST /branches/{bid}/logs/query（API key 免 CSRF；cookie 需 CSRF）：支持 logql 仅 line filters（pipeline stages 拒）；**label 白名单校验**（fields 端点 4 个：service_name/severity_text/scope_name/entity_type；未知 label → 400 "unknown label; call the log fields endpoint"）
- 日志内容 = 自己分支的平台操作日志（neon-storage/neon-function 实例 API 调用：operation/object_key/remote_ip/request_id/http_status；severity 仅 INFO）→ 无跨租户数据
- fields/{field}/values 枚举可用

### 7.5 Snapshots / 其他
- snapshots 空列表；restore body 支持 target_branch_id（项目内）
- **结论：无新洞。数据面（AI/S3）入口 WAF 封锁、Credentials 无越权、Logs label 白名单、Snapshots 空。控制面技术面 sweep 完成**

---

## 8. ��ܼ�������ɨ�裨_n1~_n13�������պ�

### 8.1 ���ָ��
| ��� | ��� | ����λ�� |
|---|---|---|
| Neon Auth | Fastify + Better Auth(��ȶ���) | ����Ŀ neonauth �� |
| OAuth �������� | Fastify(404 JSON ͬ��ʽ) | neonauth.us-east-2.aws.neon.build(����,4 provider callback ��) |
| Data API | PostgREST ���ݲ�(������ PGRST202/205 ԭ��) | *.apirest �� |
| ������ IdP | Keycloak(realm: staging-realm + master �ɴ�) | console-stage.neon.build |
| ������ | Go + Gorilla CSRF | console API |

### 8.2 Keycloak ��(_n1~_n6)���������ϸ�,�޶�
- openid-configuration:grant ����ȫ��(password/client_credentials/ciba/device ����);master realm ȫ�˵�ɴ�(��������ȱ����)
- �ٷ� auth URL(302 ��):client_id=neon-console, redirect_uri=https://console-stage.neon.build/auth/keycloak/callback(��ȷ������;http/βб��/����/@/˫б�ܱ���ȫ 400 ��)
- refresh_token(HS512)���� 200(�ɻỰ����Ч,2026-09-10 ǰ);userinfo 200 ���� email;introspect public 403;revoke 200
- device flow:ȫ client unauthorized_client(����);PAR 201 ����(request_uri UUID 60s,��������);registrations 403(Cloudflare challenge);/admin/* 302 Cloudflare Access(���ɴ�)
- social IDP 4 ��:github/google/hasura(OIDC)/microsoft;kc_idp_hint ��ת������ע�����;broker login ��������ȫ 400;account console 404
- ��¼ҳ kcContext �� Java ע��(�Ǵ� JSON),�޶���й¶

### 8.3 Data API JWT ��֤��(_n7)�����ֲ���֤���ƹ�
- ��֤ģ��:ǿ�� JWT bearer(�� JWT �� 400 missing authentication credentials: required authorization bearer token in JWT format;·������֤�����)
- ��ʵ JWT:EdDSA(Ed25519) kid=��Ŀ�� JWKS;payload role=authenticated Ӳ����;iss/aud=neonauth ��;900s ��Ч
- �۸ľ���:alg=none/HS256 ���/keyid=x �� 400 missing key id/jwk not found;payload role=postgres/superuser �ȴ۸� �� 400 invalid JWT encoding;��ǩ�� �� 400 signature error �� **��֤����=kid ����������+EdDSA ��ǩ,�� alg ����/�� role ע��·��**
- OpenAPI ������¶(��������֪);404 PGRST205/202 й¶ PostgREST ���ݲ����(��ʵ������)

### 8.4 Better Auth �������� 2026-06 advisory(_n8~_n9)
- �˵�������ж�����:�� body POST 400(FST_ERR_CTP_EMPTY_JSON_BODY)�� Fastify ·��ǰ��������,**������·�ɴ���**;�� body ȫ 404 �� api-key/device-flow/sso/admin ����˵�**��δע��**
- CVE-2025-61928(api-key δ��Ȩ����)/GHSA-cq3f(device flow)/GHSA-5rr4(sso ע��)������
- Ψһ����:**organization**(list/create/invite-member/accept-invitation + get-invitation 404)

### 8.5 �� Organization �� = GHSA-fmh4(CVE-2026-53514)��̬ȷ��(_n10~_n13)
- ����:emailAndPassword ��(����ɵ�¼)+ require_email_verification=false(sign-up ֱ�� emailVerified=false ����)+ organization �����(limit 10/creator_role=owner/send_invitation_email=false)
- ʵ����:na2(δ��֤)sign-up �û� secn12(δ��֤) �� na2 create org �� invite secn12 �� **secn12 ƾ invitationId POST accept-invitation �� 200 accepted**(by-ID ������ verified-email �Ž�,�� better-auth 1.6.14+ configuration-dependent ��Ϊһ��)
- **й¶��ȱʧ**:Neon ֻ��¶��С�˵㼯(�� organization/invitations|members|invites �б�˵�,��Ա/owner �� 404)�� invite ID(UUIDv4)�� API ö��;��,���ʼ�/UI �繤�ɻ� �� **������������**
- ����:Neon ��δ�� organization requireEmailVerificationOnInvitation:true,Ӧ������ better-auth ʱ��ע����Informational/Low ��ѡ,�����ɶ�������

### 8.6 GHSA-g38m(CVE-2026-53516 OAuth ��ʽ��Ԥ�ٳ�)��������,δ�����֤
- ����ȫ������:emailAndPassword �� + OAuth(google/github shared)+ δ��֤�����ע��ɵ�¼(sign-up ����ֱ֤�� 200)
- ������:������Ԥע�� victim ����(δ��֤) �� victim Google OAuth ��¼ �� <1.6.11 ����ʽ�󶨵�Ԥע����(�����߳������¼)
- **����֤**:����ʵ Google OAuth ����(callback ����Ϊ�޷��ں�ģ��)�� ��������ֶ�Э��
- Neon OTP ģʽ��������:������ע��� OTP �ʼ��� victim ����,�����¼�� enabled �򹥻��߿�ֱ��(��ȷ�� emailAndPassword ʵ�����á���ʵ������ sign-in 200 = ����)�� Ԥ�ٳֳ���������ɵ�

### 8.7 ���������
- ����(����,�Թ���):org sec-n12-org(na2 owner,secn12 member)��secn13 pending ����(2026-09-06 ����)�������û� secn12/secn13
- **����:Keycloak/Data API JWT ��֤��/Better Auth �����ȫ���պ�;organization ��Ϊ upstream ��֪��̬(�� Neon ����й¶��);GHSA-g38m Ԥ�ٳ�����������,�� OAuth �ֶ���֤**


---

## 9. org 角色越权 + Neon Functions Beta 面（_o1~_o23，2026-09-04）——均闭合

### 9.1 org member 越权矩阵——闭合
- 环境：na2(owner) + secn12(member)；org 数据**不在项目 PG**（neon_auth.member/organization/invitation 0 行——独立存储；user/session 在项目 PG）
- 端点×角色矩阵：invite-member/update-org/delete-org → member 403（YOU_ARE_NOT_ALLOWED_TO_*，服务端角色校验到位）；member 专属端点全集 404（只暴露最小端点集）
- **member 自提权（精确 memberId）→ 403 YOU_ARE_NOT_ALLOWED_TO_UPDATE_THIS_MEMBER**（member 行 id 从 accept-invitation 响应可得，id=UUIDv4 独立于 userId）；member 可正常 leave-org
- 参数变体矩阵（memberIdOrEmail/userId/email/memberId）→ 全部 400/403；slug 语义：update-member-role/remove-member 需精确 memberId
- ★ 教训：owner 基线调用 delete-org 真的删掉了测试 org（_o1 自毁）——owner 对照必须只用可逆操作
- **结论：Better Auth organization 角色模型服务端校验完整，无越权**

### 9.2 Functions 控制面（OpenAPI Functions tag 8 端点 + 部署链）——闭合
- 端点状态：GET functions list 200（Beta 在 staging 启用）；不存在 slug → 404 "function not visible on branch"（无信息泄露）；PATCH/DELETE 无 CSRF → 403（Gorilla）；slug regex 严格（小写 DNS label，大写/下划线/连字符边界/超长 → 400）
- **无 POST /functions 创建端点——POST /functions/{slug}/deployments 隐式创建**（multipart: zip + runtime=nodejs24 + environment JSON 字符串）
- zip 格式确认：zip 根 index.js（ESM default export {fetch}）+ package.json {type:module} → 4s 内 completed
- env 语义验证：deployment 响应/GET function 只回显 env **names**（值 write-only ✓）；空值 env 被剔除（= 删除语义）
- zip 异常矩阵：postinstall 脚本 → completed（**构建器无 npm install**）；zip slip（../路径）→ failed `mksquashfs build failed (HTTP 422): bad_path`（**构建管线：zip → squashfs**）；20MB zip 201 接受；无 index.js 也 completed（构建不校验 handler）
- custom-domains：A 项目 404 "custom domains not available for this project"（项目级 flag 关闭）；list 端点同 404
- 部署清理：所有测试函数已 DELETE（204）

### 9.3 ★ Functions 运行时隔离探测（module-scope 自执行 + console.log→Logs API 闭环）——隔离良好
- **部署后平台自动 invoke**（invoke begin/end 日志）→ module-scope 代码必然执行 → 探测函数方案可行（无需公网入口）
- 运行时画像：nodejs24 容器 + squashfs 挂载；eth0=192.168.221.x/31（点对点 veth，/31 对端=宿主侧）；内存 2048MiB
- env 注入（全部 branch-scoped 设计内）：DATABASE_URL(+UNPOOLED)/PGHOST/PGPASSWORD；AWS_ACCESS_KEY_ID=nak_live_*/SECRET=nsk_live_*/AWS_ENDPOINT_URL_S3=br-<bid>.storage.c-1…（对象存储凭据，**每次部署轮换**）；NEON_AI_GATEWAY_TOKEN=TELEMETRY_TOKEN=nt_live_*（同值）；NEON_AUTH_JWKS_URL/BASE_URL；NEON_DATA_API_URL；NEON_LOAD_PORT=8082/DATA_PORT=8081/MOUNT_POINT=/opt/function（本地 sidecar）
- **网络隔离验证**：
  - IMDS 169.254.169.254 / 100.100.100.200 → 全超时（隔离 ✓）
  - 对端 192.168.221.14 全端口拒绝；同段 .0-.30 无响应（无邻居暴露 ✓）
  - 出公网正常（ipify 200）；otel.c-1 内部域可达（https 464 自定义响应——公网 IP 18.119.245.208）
  - **无内部 DNS 视图**：*.c-1.us-east-2.aws.neon.build 全 wildcard 解析到同一组公网 IP（3.22.12.41/3.14.183.206/3.148.58.16——除 otel/ai/storage/独立记录外），函数内=外部一致，零 RFC1918
- 本地 sidecar：8081 DATA → catch-all 200 "ok"（任意路径/方法）；8082 LOAD → JSON 路由 API（60+ 路径字典全 404 {"code":"not_found"}——未命中，无可利用端点）
- **结论：Functions 运行时隔离实现良好（容器+点对点网络+egress 白名单+IMDS 隔离+无内部 DNS）；控制面实现安全。invocation_url 公网调用 → ALB 403（staging 边缘封锁，生产行为不可外推）。无洞**

### 9.4 环境残留更新
- org sec-n12-org / sec-o6-org / sec-o7-org 已全部删除（owner delete 200）；测试函数全清理（204）
- 无新增残留

### 9.5 结论
- org 越权面 + Functions 面（控制面+运行时）全部闭合；无新报告候选
- Functions Beta 值得在**生产**（console.neon.tech）复查 invocation 面（staging ALB 封锁不可测）；custom-domains 面需功能开放项目

## 10. 深度复核轮（V7~V19，2026-09-05）——组织/邀请全状态机 + 插件路由矩阵 + 跨主体矩阵

### 10.1 ★ 幽灵角色缺陷（'owner ' 尾随空白）——完整机制 + 判定 Informational
- **invite-member 路径**：role 校验=原始字符串精确比较（`'owner '` ≠ 精确 `'owner'` → fall-through 放行，**admin 也能邀**）；存储=不 trim 原样入库 → accept 后 member.role=`'owner '`（显示 owner 的零权限幽灵成员）
- **update-member-role 路径**（对照）：校验=归一化后比较（`'owner '` 当 `'owner'` → 需 owner 权限）；存储=trim → 两路径不一致但无提权组合（V10：admin/member 自升或升他人 `'owner '/' owner'/'owner '` 全 403；`'admin '` 200 但存 `'admin'`）
- **幽灵权限全端点矩阵**（V11）：update-org/invite/delete/update-member-role/remove-member 全 403/401；leave 200（=普通 member 行为）；set-active 403；最后-owner 保护精确计数（幽灵不计入，owner 在场无法自毁 org）
- **判定**：无提权组合、无 DoS、owner 全权可控、脏值仅 API 客户端可产生（UI 下拉不可能）、制造者本身是特权方 → **Informational（工程健壮性：invite 与 update 的校验/存储归一化不一致）**；建议产品修复 invite 路径 trim

### 10.2 已闭合面二次复核（攻击假设重审）——全部仍闭合
- **JWT jku/x5u/x5c/jwk header**（V12/V12b）：key 选择在验签之前（kid 不存在→`jwk not found`）；kid 不存在 + 任意 jku/x5u → 与对照一致；无 fetch 时序差 → **key 解析纯本地 JWKS 查表，无远程拉取** → 无任意 JWT 伪造面
- **org 写端点 CSRF/Origin 矩阵**（V13）：invite/update-member-role/update-org/remove-member/leave/delete × {evil,null,no-Origin} 全 403（INVALID_ORIGIN / MISSING_OR_NULL_ORIGIN）→ 写端点全校验；反证 token/get-session 为读端点单独漏校验
- **过期邀请 accept**（V14）：DB 回拨 expiresAt 1h → accept 400 INVITATION_NOT_FOUND（过期过滤在查询条件内）→ 过期邀请不可用

### 10.3 插件全路由矩阵（V15）——盲区歼灭
- 31 端点 × {匿名, 登录} 双态：email/session/org/admin/2FA/webauthn 全覆盖
- **存在**：change-password（200）、change-email（400 CHANGE_EMAIL_DISABLED）、delete-user/revoke-sessions/revoke-other-sessions（401 匿名）、admin/list-users（401 匿名/403 普通用户）、admin/create-user/ban-user/remove-user/set-role/revoke-user-session（400 body 校验先于认证，认证在后）、cancel/reject-invitation、list-invitations（GET）、organization/list（GET 200）
- **不存在（404）**：migrate、2FA 全部（enable/verify-otp/send-otp/verify-totp/disable/trust-device/send-otp-phone）、webauthn 全部、admin/list-sessions、organization/get-members 等 → **无隐藏插件**

### 10.4 admin 插件提权链（V16）——权限模型完整
- user 表含 role/banned/banReason/banExpires 列（admin 插件数据结构完整存在）；DB 全部用户 role='user'
- 匿名 create-user（带/不带 role）→ 401（认证在参数校验后）；普通用户 → 403 YOU_ARE_NOT_ALLOWED_TO_CREATE_USERS；sign-up 带 role → 400 FIELD_NOT_ALLOWED（字段白名单）→ 无提权路径

### 10.5 邀请撤销状态机（V17）——闭合
- cancel/reject-invitation × Origin 矩阵：evil/null/no-Origin 全 403（Origin 中间件覆盖；V15 的匿名 400 仅 body 校验顺序在前）
- reject → status='rejected' → 再 accept 400 INVITATION_NOT_FOUND（不可恢复）；member 跨权 cancel → 403 YOU_ARE_NOT_ALLOWED_TO_CANCEL_THIS_INVITATION
- list-invitations：仅 org owner/成员可列；受邀者（非成员）不可

### 10.6 ★ 跨主体矩阵（V19/V19b）——真授权边界，全部拦截
- **无关用户 × 他人 org**（U1 操作 U2 的 orgB）：list-invitations 403（非成员）；invite/update-role/leave/remove-member 400 MEMBER_NOT_FOUND（先查成员关系）；update/delete 400 USER_IS_NOT_A_MEMBER_OF_THE_ORGANIZATION → 每次操作前验证调用者成员身份
- **跨身份 accept**：U2 accept U3 的邀请 → 403 YOU_ARE_NOT_THE_RECIPIENT_OF_THE_INVITATION（邀请与登录身份绑定）；状态保持 pending；受邀者本人 accept 200
- **跨身份 reject**：U3 reject U2 的邀请 → 403 同源（YOU_ARE_NOT_THE_RECIPIENT）；受邀者本人 reject 200 → status='rejected'

### 10.7 console-stage 注册解锁尝试（V18）——环境关闭
- /api/register 存在但 CSRF 三轮 403；Keycloak register 页 404 → **staging 自注册关闭** → 第二控制面账号不可得 → 跨账号 IDOR（permissions/transfer 语义链）无法闭环，理论残余面被环境锁死

### 10.8 环境残留与最终结论
- 所有测试 org（v7b/v9/v10/v11/v13/v14/v17/v19 系列）已删除，stray orgs 清理完毕（含 V13 崩溃残留 2 个 + v9-org 1 个），孤儿 pending 邀请已清 → 环境干净
- **最终结论：Neon Auth（魔改 better-auth）技术面经 3 轮交叉验证（功能矩阵→攻击假设重审→跨主体矩阵）无安全后果；可提交候选仍为零**
- 工程反馈（均 Informational）：① 幽灵角色（invite 不 trim + 校验 fall-through）；② verify-email 端点缺失（OTP 无法消费，功能半残）；③ invite/update 校验归一化不一致
- 残余理论面：console 跨账号语义（需第二账号，staging 关闭）；Functions invocation 生产复查；custom-domains 功能开放项目

## 11. 经典攻击类别补测轮（V21~V24，2026-09-05）——用户点名四类全闭合

### 11.1 CSRF：Content-Type × Method × Origin 三维矩阵（V21）——封死
- **Content-Type 白名单**：invite-member × {text/plain, urlencoded, multipart, no-CT, xml, json+gzip} × {evil/no-Origin} → 全 415（两种 415 风格：better-auth `UNSUPPORTED_*` vs Fastify `FST_ERR_CTP_INVALID_MEDIA_TYPE`——双解析层均拒）→ **浏览器 form 提交（非 application/json）无法到达 handler** → 无 CT 绕过 CSRF
- charset 变体（`application/json; charset=utf-16`、`Application/JSON`）→ 按 JSON 解析 → Origin 检查在（403）✓
- **Method 混淆**：PUT/PATCH/DELETE/HEAD × invite-member → 404（严格 method 路由）；OPTIONS → 400 Invalid Preflight Request → 无 method 漏挂中间件
- 结论：CSRF 防线 = Origin 校验（写端点全有）+ CT 白名单 + 严格 method 路由，三层互补无空隙

### 11.2 SSRF 面盘点（V22/V22b）——无 fetch-URL 参数
- **org logo URL**（update-org data.logo）：http://127.0.0.1:1 / IMDS 169.254.169.254 / httpbin / file:// 全 200 **纯存储**（0.25-0.51s 无 fetch 时序差）→ 无服务端拉取
- **OAuth provider**：6.1 已确认仅 google/github type=shared（Neon 托管客户端）→ 无自定义 issuer；PATCH auth/config 试 oidc/custom type → 400 schema（name field required，无法最小 body 探测——全量替换语义）→ 无 discovery fetch 面
- **legacy email_server**：POST/DELETE → 405（只读端点）→ 无 SMTP host 回连面；webhooks 关（6.1）
- 结论：Auth 技术面**无任何接受 URL 并由服务端 fetch 的参数**（jku/functions egress 已另行闭合）→ 无 SSRF

### 11.3 ★ 变异 URL（V23）——库名路由参数不校验 + Host 子域模式校验缺口（均 Informational）
- **库名前缀**：`/neondb/auth/*` 200（路由参数=库名，不做存在性校验）；`/postgres/auth/*` → **500 DATABASE_ERROR `relation project_config does not exist`**（postgres 系统库命中 handler 后 SQL 崩溃 → **泄露内部表名 project_config + PG 错误细节**）；main/db2/neondb2/NeonDB/neon%64b → 404 Database unavailable → 500 仅错误处理问题（信息泄露级 Informational，无数据）
- **Host 变异**：裸域（neonauth.us-east-2...）→ 400 INVALID_HOSTNAME（**白名单校验存在**）；UPPER 大小写 → 200 正常；尾点 → SSL hostname mismatch（CDN 证书）；`x-<分支host>`（子域模式）→ **500 pino 内部错误**（`Cannot read properties of undefined (reading 'Symbol(pino.m...')`——子域模式 Host 绕过裸域白名单到达应用层后 endpoint 解析崩溃）→ 无 handler 数据可达，错误处理级 Informational
- 结论：路径/库名/Host 变异均无法触达他人数据；两条 500 错误处理反馈

### 11.4 变异 body（V24/V24b）——schema 严格 + trim 覆盖 Unicode，无解析器分歧
- **类型混淆**：memberId=123/null/[array] → 400 Zod `VALIDATION_ERROR [body.memberId] Invalid input: expected string`（schema 严格类型检查）
- **Unicode 空白 role**（owner+U+3000 / U+00A0 NBSP / U+2003 EM）：update-member-role 200 但 **DB 终值 role='owner'**（服务端 trim 处理 Unicode 空白，非 ASCII-only）→ 幽灵角色无 Unicode 变体（V9 幽灵仅限 ASCII 空格且零权限）
- **重复 key**：`{role:owner,role:member}` 及逆序 → 200，JSON 解析器折叠取**最后一个**（DB 终值与最后 key 一致）→ 无校验/执行双解析器分歧 → 无绕过
- 额外字段（admin:true）→ 静默忽略（无字段白名单问题——角色仅经 memberId 定位）
- 附带修正：accept-invitation schema 已从 organizationId 改为 **invitationId 必填**（400 body.invitationId expected string）——端点语义演进，与 V19 记录一致（当时亦用 invitationId 拿 recipient 403）

### 11.5 环境清理
- V21-V24 全部测试 org（28373c7d/v22 系列/cd777a92/29af6bc0/cf373aa2/a8c5a2c7）API 删除 + DB purge；孤儿邀请/孤儿 member 行全清 → **DB organization/member/invitation 三表零残留**

### 11.6 结论
- 用户点名的 CSRF/SSRF/变异 URL/变异 body/变异 Content-Type 五子类全部系统补测闭合：**无安全后果**
- 新增 3 条 Informational 工程反馈：① /postgres/ 库名 500 PG 表名泄露；② x- 前缀 Host 500 pino 内部错误（子域模式校验缺口）；③ accept-invitation 参数语义变更（organizationId→invitationId，无兼容层，旧客户端 400）

## 12. 表名泄露利用链追查（V25~V26，2026-09-05）——顺藤摸瓜到 jwks 私钥，链断于 KMS 信封加密

### 12.1 project_config 定位（V25）——纯配置镜像，无敏感
- `/postgres/auth/*` 500 泄露的表 = `neon_auth.project_config`（仅 1 行）：列 = trusted_origins/social_providers/email_provider/email_and_password/allow_localhost/plugin_configs/webhook_config
- 内容 = 控制面 auth 配置的 DB 镜像（与 §6.1 API 画像一致）→ **无密钥字段** → 泄露面 = 配置值（API 已可读）+ 表名（内部 schema 结构线索）
- 库名 SQL 字符探针（`postgres'`/``/`;`/`--`/`%27`/`%00`/``


## 12. 表名泄露利用链追查（V25~V26，2026-09-05）——顺藤摸瓜到 jwks 私钥，链断于 KMS 信封加密

### 12.1 project_config 定位（V25）——纯配置镜像，无敏感
- /postgres/auth/* 500 泄露的表 = neon_auth.project_config（仅 1 行）：列 = trusted_origins/social_providers/email_provider/email_and_password/allow_localhost/plugin_configs/webhook_config
- 内容 = 控制面 auth 配置的 DB 镜像（与 6.1 API 画像一致）→ 无密钥字段 → 泄露面 = 配置值（API 已可读）+ 表名（内部 schema 结构线索）
- 库名 SQL 字符探针（引号/分号/注释/%27/%00/反斜杠 等 13 种）→ 全 404/400（参数化查询，无注入）；template0 → 500 连接超时、template1 → 同 project_config 500（库存在性 oracle 仅限自己 endpoint → 无跨租户）

### 12.2 neon_auth.jwks 表：Data API JWT 私钥落库（V26）——链断于信封加密
- 表结构：id/publicKey/privateKey/createdAt/expiresAt；1 行，publicKey = Ed25519 JWK
- 决定性关联：真实 /token JWT 的 header kid=6ab964bf... = jwks 表 id；用存储 publicKey 验签真实 JWT → VALID（该 keypair 就是 Data API JWT 签名者）
- privateKey 列：JSON 编码的 338-hex 字符串（169 bytes 随机二进制）→ 解析全失败：前/后/滑窗全 32B seed 窗口派生公钥均不匹配、DER 载入失败、非双层 hex → KMS 信封加密密文（明文私钥在 Neon 服务端）
- 权限矩阵：新建低权限 role（LOGIN+CONNECT+USAGE）→ SELECT neon_auth 全 9 表 → 全 DENY（schema 表权限仅授 owner）→ 跨主体无门；owner 读到的只是密文 → 伪造链断
- 结论：私钥加密落库是 Neon 安全设计（可恢复性/多区域），DB owner 无法提取明文 → 无 JWT 伪造；测试 role 已 REVOKE+DROP
- 补充观察（Informational）：Data API 签名私钥密文存在于用户 DB——若未来 KEK 管理失当或加解密端点出现，此面需重审；当前无利用路径


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
