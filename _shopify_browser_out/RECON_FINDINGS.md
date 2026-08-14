# Shopify 匿名侦察发现(2026-08-13)

## 项目要点
- H1 项目: hackerone.com/shopify, 测试账号必须用 pccp@wearehackerone.com 注册
- 只测自己创建的 store;禁止测真实商家;禁止联系 Shopify Support
- 核心资产: your-store.myshopify.com / admin / accounts / partners / shop.app / arrive-server.shopifycloud.com / Authentication & ATO(2026-06新增,报告仅1例)
- 赏金: Low $500-1k / Medium $1k-14k / High $14k-50k / Critical $50k-200k

## 主攻面: auth.shop.app GraphQL(Shop app Web 客户端,Core/Critical)

### 入口
- Web 客户端: https://auth.shop.app/ (Remix SPA, JS 已下载 658 文件 12MB 到 js/)
- GraphQL 端点: POST https://auth.shop.app/web/api/graphql
- 必需请求头:
  - `X-Device-Id-Hw`: clientToken(匿名发放,来自 HTML window.process)
  - `Session-Id`: sessionToken(匿名发放)
  - `x-graphql-operation-name`: 必须匹配操作名,缺失=401
  - Cookie: _shop_app_essential 等(访问首页获得)
- 限流: 严格 IP 级长窗口("Slow down there partner" 429),大量请求会封 IP 窗口

### 已确认
- 匿名 GraphQL 可执行: User(匿名变体返回 userPrivacySettings/currentJurisdiction)、PayShopCashBalance(无 pay account)
- 需登录: AgentStreamUrlCreate 等(UNAUTHORIZED)
- 匿名无法 introspection(__schema 被拒)

### 148 个操作/105 个查询定义(js/ 下载 + graphql_ops.json)

### 高价值 IDOR 候选(需登录双账号验证)
| 操作 | 参数 | 影响 |
|---|---|---|
| GetBuyerContext | conversationId: ID! | 读他人 AI 记忆(buyerMemories)/活跃购物车(activeCarts)/最近搜索(recentSearches)/设备 |
| AgentConversations/Messages | - | AI 对话数据 |
| OrderDelete / OrderMarkAsDelivered / OrderUnmarkAsDelivered | orderId: ID! | 操作他人订单 |
| DeletePaymentCard / UpdatePayPaymentCard | id: ID! | 他人支付卡 |
| PayAddressDelete / PayAddressUpdateMutation | id: ID! | 他人地址 |
| EnableAutopay / DisableAutopay / InstallmentsPaymentDisclosure | payOrderId: ID | 他人分期订单 |
| DeviceAuthorizationRevoke | deviceAuthorizationId: ID! | 撤销他人设备授权 |
| BuyerProfileAvatarSet / DeleteProfile / UpdateProfile | profileId: ID! | 他人 profile |
| ProductListRename / ProductListRemove / SettingsUpdate | id: ID! | 他人产品列表 |
| ProductListJoinMutation | publicId+inviteToken | 邀请加入他人私有列表 |
| ShopCashRewardVoucherCampaignClaim | handle+voucherCode | 领取 Shop Cash 奖励(抽奖链接机制) |
| AgentDeleteConversation / ConversationMetadataUpdate | conversationId | 他人 AI 对话 |

### REST 端点(auth.shop.app)
- POST /web/api/support-token → 403 需登录(客服 token)
- /web/api/user、/web/api/agents/classification、/web/api/agents/overrides、/web/api/shop-by-product-id?productId=
- /web/random-product、/web/auth/logout、/web/auth/email/complete(OAuth 邮箱连接,gmail/outlook)

## 其他面(已关闭)
- accounts.shopify.com: Cloudflare 硬墙,curl 全部 403,必须浏览器
- *.shopifycloud.com 内部服务: Minerva SSO 墙(asynqmon/oxygen/observe-ai 等全部重定向)
- go/open/tap/meet.shop.app: 营销归因短链,目标固定 shop.app,无利用面
- server.shop.app / server-v4.shop.app: arrive-server 后端占位页
- routing-foundations-gateway: 健康检查页 "hey!"
- linkpop.com: 根域 301 到 shopify.com

## 下一步候选
1. 等 GraphQL 限流窗口(IP 级)恢复 → 测 operationName 白名单强度(修改查询文本是否被拒/可扩展字段)
2. 浏览器操作: 注册 Shopify 账号(pccp@wearehackerone.com)→ 登录后:
   - 双账号验证 GetBuyerContext conversationId IDOR(最高优先)
   - 抓登录态真实 GraphQL 流量对比匿名面
3. GitHub 源码审计(leaked credentials 有赏金): 搜索 shopify 组织仓库硬编码凭证
4. myshopify.com 公开商店面: storefront GraphQL 未发布产品泄露
