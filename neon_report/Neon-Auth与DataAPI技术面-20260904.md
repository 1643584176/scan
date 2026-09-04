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
- **й¶��ȱʧ**:Neon ֻ��¶��С�˵㼯(�� organization/invitations|members|invites �б��˵�,��Ա/owner �� 404)�� invite ID(UUIDv4)�� API ö��;��,���ʼ�/UI �繤�ɻ� �� **������������**
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
