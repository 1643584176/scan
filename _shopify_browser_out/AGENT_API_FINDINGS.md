# Shop AI Agent API 面发现(2026-08-13 第二轮)

## 核心突破:AI Agent 完整文档面(匿名可读,公开设计)
- GET https://auth.shop.app/SKILL.md — Shop CLI Agent 操作手册(16.8KB)
- GET https://auth.shop.app/references/direct-api.md — 认证/checkout/订单 API 细节(9.6KB)
- GET https://auth.shop.app/references/catalog-mcp.md — Global Catalog MCP 调用规范(10KB)
- GET https://auth.shop.app/references/safety.md / legal.md
- GET https://auth.shop.app/.well-known/agent-skills/index.json — Agent Skills 发现文档
- 引用链: /.well-known/agent-skills/index.json → /SKILL.md → /references/*.md(agentskills.io 协议公开发现)

## 泄露的关键凭证/端点(client_id 硬编码在公开文档)
- OAuth client_id: 5c733ab2-1903-400a-891e-7ba20c09e2a3(scope: openid email personal_agent)
- POST accounts.shop.app/oauth/device — device-code 匿名可用(200)
  - user_code: 8 位大写字母(26^8,不可枚举)
  - device_code: 43 字符随机
  - expires_in: 900s, interval: 5s
- POST accounts.shop.app/oauth/token — device_code/refresh_token grant
- GET accounts.shop.app/oauth/userinfo — Bearer 验证(匿名 401)
- POST shop.app/oauth/token — token-exchange grant(resource=https://{shop_domain}/, mint 任意 merchant 的 checkout JWT)

## UCP(Universal Checkout Protocol)面
- POST https://catalog.shopify.com/api/ucp/mcp — **匿名可用**,仅 3 工具:
  - search_catalog(匿名可搜,间歇性返回空 products——疑似多实例/缓存)
  - lookup_catalog(任意变体/产品 ID → 完整产品数据,含 seller 内部 ID/域名/checkout_url)
  - get_product
- 其他工具(create/complete/update_checkout 等)→ Tool not found(仅 merchant 域 /api/ucp/mcp 可用)
- auth.shop.app/api/ucp/mcp → 410 Gone(已移除)
- profile: https://shopify.dev/ucp/agent-profiles/2026-04-08/personal_agent.json
  - 其他 profile 枚举(admin/merchant/staff 等)→ 全部 404
- OpenRPC schema: https://ucp.dev/2026-04-08/services/shopping/mcp.openrpc.json(13 方法)
- checkout.json schema: 状态机(incomplete→ready_for_complete→completed)
- **变体 ID 枚举**: gid://shopify/ProductVariant/50362300006715 有效,相邻 ±100/±1000/±10000 全空,
  数量级跨度全空 → ID 空间稀疏,枚举不可行

## 产品数据泄露(匿名 lookup_catalog)
- 完整字段: title/description/metadata(ML 推断)/media/variants(price/availability/url/checkout_url)/
  seller(id=gid://shopify/Shop/15044320, domain=pzdea.myshopify.com)
- checkout_url 带 _gsid 参数(guest session 追踪)
- 结论: 公开数据(设计功能),非漏洞

## OAuth device-flow 验证
- 匿名可发起 device-code 请求(200)
- user_code 8 位大写不可枚举;轮询需 device_code 配对;无绕过

## FedCM(支付身份联盟)端点图
- GET https://shop.app/pay/fedcm/config.json — 完整配置(200)
- accounts/assertion/metrics → 401 需登录;revoke → 404
- clientmetadata → 200(公开元数据)

## REST 端点补充(全部需要登录或 429)
- /web/api/support-token → 400 {"message":"Unexpected Server Error"}(后端依赖故障)
- /web/api/available-feature-flags → 200 {"featureFlagsAvailable":[],"error":"User not found"}(匿名)
- /web/api/caller-identification-signature → 429(与 GraphQL 共享限流池)
- /dev/url-proxy、/dev/agent-proxy、/ci/shopkick-stream-proxy、/dev/guest-signin → 404 已禁用
- /email/open → 200 PNG 追踪像素(无参数也返回)
- /sid/{shopId} → 302(shop ID 路由)

## 新子域测绘
- mail.shop.app: Rails 服务(404 page not found),全路径 404,无面
- a.shop.app: 短链 302
- preview.shop.app: 不可达(000)
- help-shop-app-staging*.shop.app: 302(5 个 staging,未深入——可能第三方)
- discover/download/get/www.shop.app: 301 → shop.app

## 环境/内部信息
- 生产代码硬编码 wss://shop-server.shop.dev/ws(DevFeedReloadChannel,仅 feedId=sandbox 启用,
  域名解析 127.255.255.0 公网不可达)
- shop-server.sfe.shopifyinternal.com / web-shop-client.shop.dev: 不可达
- otlp-http-production/staging.shopifysvc.com、monorail-edge.shopifysvc.com: 公网可达(404 根路径)
- frontend-event-collector.shopifysvc.com: 公网超时(仅内网)
- K8s 内部地址: http://collector.tracing-production-proxy.svc.cluster.local.:4317

## 当前状态
- GraphQL 限流已恢复,但匿名请求被网关 401 拦截(空 body)→ 需要登录会话
- 直连 IP 被 Cloudflare WAF 403;代理 IP 正常(仅 GraphQL 需认证)
- /web/api/* 重新扫描: available-feature-flags 200、cart 200(Unauthorized 错误)、user 500、
  support-token 400、其余 429(共享限流池,易触发)

## 第三轮新发现(agent API web 代理面)
### /agents/* 路由家族(manifest 确认 8 条,Remix SSR 服务器端实现)
- **/agents/search GET 匿名可用**(text/markdown,ACAO:*):
  - ?query= → 产品搜索(与 catalog 一致,公开数据;间歇性空响应=多实例负载均衡)
  - POST similarTo={id: GID} → 相似搜索(公开数据);id 无效 → "**id**: Not found (404)" 可探测 ID 存在性
  - similarTo={media:?} 格式未破(400 [object Object]);media 应为 base64,具体结构未知
- **/agents/orders/by-shopify-id 匿名可达订单服务** ⚠️ 潜在 IDOR:
  - ?shopifyOrderId=N → 无效 ID 统一 500 {"error":"Failed to fetch order"}
  - 空 → 400 required;非数字 → 500;POST → Unexpected Server Error
  - **未验证有效 ID 是否返回数据——需要真实订单 ID(自己下单)**
- **/agents/returns**: product_id 参数(数字 ID)→ "discovery product not present";GID → Invalid
- /agents/auth/device-code: POST → 502 Service unavailable(稳定故障,后端不可用)
- /agents/auth/token: POST → 400 invalid_grant(活路由;不认 accounts.shop.app 的 device_code,
  独立 token 系统)
- /agents/auth/userinfo: GET → 401 "Authorization header is required"(活路由)
- /agents/orders: GET → 401(需认证)
- /agents/orderSearch: 404(manifest 有但被禁用/移除)
- **新端点线索**: agents.orders.by-shopify-id、agents.returns 均不在 manifest 的 8 条里?
  (manifest 只有 auth.*/orderSearch/orders/by-shopify-id/returns/search 8 条)

### 后端服务测绘
- **server.shop.app**(Rails,ShopServer): 根 200 带 CSRF;healthz 200;/api/* 全 410 api_gone
  (网关整体禁用);/internal/* → Minerva SSO;Host: shop.app → 403(host 校验)
- **shopkick.shopify.ai**: /healthz 200;/internal/* → Minerva SSO;robots.txt 默认
- **minerva.shopifycloud.com**: /auth/minerva?rd= → 302 shopify.okta.com(内部 SSO,
  rd 不回显、无 open redirect;泄露 okta client_id=0oalkvlxz1CcOw9LO0x7)
- **accounts.shop.app/oauth/device 匿名正常**(标准 device flow,user_code 8 位大写)
- 授权页 /oauth/device_code?user_code= → 200(bot 检测 meta client-is-bot)
- CSP 上报: security-reports.shopifysvc.com(内部)

## 待做(需登录/注册)
0. **最高优先**: 注册测试账号(pccp@wearehackerone.com)+ 创建测试 store + 下测试单
   → 验证 /agents/orders/by-shopify-id 是否匿名返回订单数据(若 200 → 匿名 IDOR 直接可用)
1. 双账号 IDOR: GetBuyerContext(conversationId)最高优先
2. 自己 store: /api/ucp/mcp 工具全集 + /.well-known/ucp 发现 + checkout 流程
3. device-code 授权后: /pay/agents/payment_tokens、/agents/orderSearch(x-device-id 注入面)
4. token-exchange 的 resource 参数校验(resource=https://{shop_domain}/ 任意域名?)
