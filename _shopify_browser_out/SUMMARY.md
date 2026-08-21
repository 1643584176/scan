# 会话总结:Shopify MCP SSRF 深化(2026-08-13)

## 一句话总结
MCP `profile` 参数 SSRF 从盲打升级为**内网 JSON 数据读取级**,证据链完备可报 H1;profile 注入攻击链(潜在 Critical)卡在"公开可 GET 的 JSON 载体"最后一环。

## 本会话完成的工作

### 1. SSRF 校验链完全逆向(错误分类 = 信息泄露通道)
- 通过 8 类错误信息精确重构服务端校验逻辑: 协议白名单 → URL 格式 → content-type → Cache-Control → JSON 解析 → 状态码/DNS/连接分类
- 关键突破: `Cache-Control` 规则精确化(必须有 cc 头且不含 no-cache/private,纯 max-age 即可通过)——用 jsonplaceholder 对照验证,而非猜测

### 2. 内网枚举(数据读取级证据)
- `shop-server.sfe.shopifyinternal.com` 的 OIDC 端点返回 "Missing ucp version" → **内网 JSON 被服务端完整 fetch+解析**,SSRF 不再是盲打
- 15 个内网子域 DNS 确认(admin/api/checkout/catalog/ucp/graphql/metadata/store/web 等)
- `/healthz` 系 2xx、`/api` 系 Connection timeout(路由存在)、仅 443 开放
- 封死方向确认: 重定向不跟随、metadata 不可达、协议白名单

### 3. Profile 注入载体探索(攻防最精彩部分)
- 确定注入三条件: 内容可控 + ct=application/json + cc 有效 + 公开 GET
- 系统性排除: webhook.site(头固定+付费墙)、uguu(无 cc)、0x0.st(503)、paste.rs(ct 不对)、jsonblob(403)
- 挖通 StagedUploadsCreate persisted query(从 render.js AST 提取 hash)→ 拿到 GCS 预签名 URL → bare PUT 上传成功 200
- 私有桶死路确认: 签名 URL PUT-only(GET 403)、acl=private 强制、拼参数/加头破坏签名 → **完整理解 GCS 签名机制**
- 主题 asset 上传撞 CHALLENGE_REQUIRED(Identity Session User Verification),API 不可绕过

### 4. 关键技术资产
- admin GraphQL persisted query 调用方式(hash + 操作名 + shop 路径 + CSRF)
- StagedUploadsCreate hash 已固化;商品图片 CDN 载体思路(按扩展名返回 ct)待验证

## 关键教训
1. **错误信息是最高效的信息泄露通道** —— 把校验链的每个错误分类当作探测信号,而不是"测试失败"
2. **已知行为服务对照法** —— 校验规则用已知服务精确化,不在未知服务上猜(避免 uguu 无 cc 被拒时的误判)
3. **载体优先找目标自己的 CDN** —— 托管服务全是坑(付费墙/头固定/关闭),目标 CDN 按扩展名返回类型 + cc=public 是最干净路径
4. **云存储签名 URL 机制**(通用): 签名只覆盖 host+method、PUT-only、acl 签名强制 —— 这类 URL 永远不能当读取载体
5. **CHALLENGE_REQUIRED 是人机边界** —— 涉及 Identity 验证的写操作,自动化到此为止,要么请用户浏览器完成,要么换载体

## 下一步(见 PROGRESS.md)
1. 商品图片 `filename=profile.json` CDN 载体测试(恢复点)
2. 失败则走 jsDelivr(需 GitHub 账号)
3. SSRF 报告提交 H1
4. profile 注入闭环 → 单独 Critical 报告

---

# 会话总结: Profile 注入链最终裁决(2026-08-19)

## 一句话总结
Vercel 载体打通了 profile 注入链(最后一环),但注入边界被完全确定:工具可见性 = profile capabilities ∩ 服务端允许集(交集模型),无法提权;SSRF 报告按官方规则维持不提交;仅剩认证态测试一条路。

## 本会话完成的工作

### 1. 载体突破: Vercel 静态部署(替代所有 CDN/GCS 方案)
- 用 `vercel_cookies.txt` 里的 Bearer token 直接调 Vercel API/CLI 部署 profile.json → 一次性通过全部校验(ct=application/json + cc=public + 公开 GET + 内容可控)
- **v13 API 部署坑**: files 会进 `src/` 子目录导致 404;改用 `npx vercel deploy --prod --yes --token <vcp>` CLI 部署到根目录
- **可达性坑**: deployment URL(带随机段)本机/代理不可达,alias URL 可达;Shopify 服务端两者都可达(0.9s 响应=连通)
- 部署载体: `https://mcp-carrier-2.vercel.app/profile.json`

### 2. 注入边界完全确定(交集模型)
| 实验 | 结果 | 结论 |
|---|---|---|
| 注入 profile(无 catalog.search)+ search_catalog | Tool not found | profile capabilities 控制工具可见性 |
| 注入 profile(含 catalog.search)+ search_catalog | 正常执行 | 同上 |
| 官方 profile + create_checkout/get_order | Tool not found | checkout/order 有服务端认证门槛 |
| 注入 11 个 merchant/admin capability 名 | 静默丢弃 | 白名单强制交集 |
| spec/schema → webhook.site | 无新请求 | 不 fetch,无二次 SSRF |
| payment_handlers 注入 | 不回显 | 无影响 |
| 成功响应 structuredContent.ucp | 回显规范化 capabilities | 白名单指纹通道(无越权价值) |

### 3. 内网证据面收尾
- 14 主机 × 11 路径批量枚举(154 请求): 只有 shop-server 2 个 OIDC JSON 端点,13 主机 healthz 2xx 非 JSON,web.sfe 全路径 HTML catch-all
- 服务端 fetch 请求头(webhook.site 记录): UA=Shopify-UCP/1.0,**无 Authorization/cookie** → 凭据窃取不可行

## 关键教训
1. **载体优先级: 用户已有账号的托管平台 > 目标 CDN > 第三方 paste 服务** —— Vercel(用户已有账号)比商品图片 CDN 快得多,不用重新抓 admin cookie
2. **Profile 注入的边界判定法**: 工具可见性 = 注入 capabilities ∩ 服务端允许集。先测"官方 profile 能否调用目标工具"(认证门槛),再测"注入能否扩张"(白名单)——两步即可裁决注入是否有价值
3. **structuredContent 回显 = 服务端白名单指纹**: 成功响应回显规范化 capabilities,注入的名字留下=被接受,消失=被丢弃——不用盲猜白名单
4. **SSRF 报告门槛复盘**: 内网 JSON 解析+子域枚举+内容读取都不够,Shopify 只要元数据/凭据/提权链——证据再完备也过不了规则关,省下报告机会

## 下一步(2026-08-20,见 PROGRESS.md)
1. 认证态测试(唯一剩余方向): shop.app 登录抓 Cookie → token-exchange → MCP 认证调用 → checkout/order/cart 是否出现 → payment_handlers 注入真实影响
2. 无新发现 → 此线封死,回 Figma

---

# 会话总结: 认证态测试完成,全线闭环(2026-08-20)

## 一句话总结
官方 OAuth Device Flow 拿到真实认证态后,在 merchant 域(fluxfootwear.com)突破到完整工具集,但 create_checkout 是官方正常功能,注入只能收缩不能扩张——Shopify 线彻底封死,无提交价值。

## 本会话完成的工作

### 1. 认证态获取: 官方 OAuth Device Flow(替代抓 cookie)
- `POST accounts.shop.app/oauth/device`(client_id 5c733ab2-1903-400a-891e-7ba20c09e2a3, scope openid email personal_agent)→ 用户浏览器授权 → 轮询 `/oauth/token` → access_token + refresh_token(1h 可续)
- 验证: `GET /oauth/userinfo` 200(email/phone 均 verified, sub=JC4wRdKKZLim3nmR54SJJLYp)
- 坑: 授权码 10 分钟过期(超时重发)、授权页 403(CF 路径级拦截,需完整链接+无痕窗口,accounts.shop.app 可达而 shop.app/login 403)、Passkey 登录卡住(改用密码/邮箱验证码)、手机号 +891 无效(改 +86)
- token 保存: `_shop_app_token.json`;**以后恢复认证只需重跑 `_shop_app_device_auth.py` + 用户浏览器点授权,无需抓 cookie**

### 2. token-exchange 两种变体(都成功)
- catalog token: `audience=api.shopify.com` → 发往 catalog.shopify.com
- checkout JWT: `resource=https://{shop_domain}/` → 发往 merchant 域 UCP(返回 shop-token-exchange+jwt)

### 3. catalog 域认证态 = 匿名态(8-19 "认证门槛"误判修正)
- tools/list 认证态 vs 匿名: 都只有 search_catalog
- 5 个高权工具 × 官方/注入 profile: 全部 Tool not found
- 结论: catalog 域**根本没有** checkout/order/cart 工具——不是认证门槛,是端点域不对

### 4. merchant 域(真实商店 fluxfootwear.com)完整验证
- 商店提取链: search_catalog(compact 不带 seller)→ get_product → variants[].seller.domain → fluxfootwear.com(variant 44292830167273)
- checkout JWT → tools/list 返回完整工具集: get_checkout/create_checkout/get_order/get_cart 等
- **create_checkout 官方/注入都真实成功**: 返回 checkout id + continue_url + gpay payment_handlers(merchant_name "Flux Footwear")
- get_checkout(`{"id": cid}`) 成功返回自己的 checkout 详情
- **payment_handlers 注入无效**: 响应回显商店真实 gpay 配置,注入 URL 被服务端配置替代
- **交集模型收缩验证**: carrier4(只声明 order+catalog.search)→ create_checkout/get_checkout "Tool not found",search_catalog 正常——只能收缩不能扩张,双向确认
- **二次 SSRF 排除**: carrier3(spec/schema→webhook.site)× merchant 域 → create_checkout 成功但 webhook.site new=0
- **IDOR 排除**: checkout id 带 `?key=32位随机hex`,不可枚举
- 字段对比(35/132 差异): payment_handlers 两者相同;messages 配送错误为随机性(官方复测无)
- shop.app API: payment_tokens 200(空数组无预算);orderSearch 被 CF 路径级拦截(与 token 无关)

## 关键教训
1. **Device Flow 是获取认证态的标准方式**——比抓 cookie 干净可靠,用户只需浏览器点一次授权;失败多为授权码过期/路径级 403/Passkey,可逐一排除
2. **端点域决定工具集**: catalog 域只有 catalog 工具,merchant 域才有 checkout——测"认证门槛"前必须先确认端点域,否则会误判
3. **交集模型两域验证完成**: 注入只能收缩不能扩张——判定"注入是否有价值"的通用两步法: 官方 profile 能否调用目标工具(认证门槛)+ 注入能否扩张(白名单)
4. **突破到完整工具集 ≠ 漏洞**: 认证态下工具真实可用,但要逐项确认是否官方正常功能;payment_handlers 服务端优先、key 随机不可枚举、无二次 fetch——边界全部确认

## 下一步(见 PROGRESS.md)
无——Shopify 线彻底封死。恢复 Figma 主线(2026-08-19 状态: identity-claim 报告已关闭;候选: livegraph mutation 写操作、AiMeterUsageView、custom tools 401 根因)
