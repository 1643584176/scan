---
name: mediator-token-chain
description: 多域同构 OAuth 架构下批量获取各域 access_token 并测绘服务面的技能。用于收购合并后共享身份的多域平台（如 Superhuman×Grammarly），用已登录 cookie 直通各域 mediator 链拿 aud 不同的 token，从前端 JS 提取完整服务配置（api.* 服务面、staging/QA 环境链），并按 Fastify/Spring 错误语义分类推进攻击面。核心信念：同架构多域共用同一身份，aud 决定网关权限，前端环境配置是攻击面地图。
---

# 多域 Mediator OAuth Token 链与服务面测绘（Mediator Token Chain）

## 适用场景

目标平台存在同构多域架构且共享身份系统（典型：收购合并后，如 Superhuman 收购 Grammarly，id/tokens/account/settings 多域共存）：

- 每个域有自己的 `/v1/mediator/initiate` → OAuth → `/v1/mediator/token` 链
- 各域签发的 token 的 `aud` 不同 → 决定可访问的网关
- 前端 JS 内嵌完整环境配置（api 服务面、staging/QA 域、client_id）

**核心洞察**：不需要重写 OAuth 流程——已登录的 IdP cookie 让 authorize 直接 307 带 code 回调（免交互）。每个域 3 个请求拿一个 token。

## 步骤 1：从前端 JS 提取 mediator 配置

在目标域的主 bundle 中搜索：

```
tokenPath:"/v1/mediator/token"   # token 端点
loginPath:"/v1/mediator/initiate" # initiate 端点
authBaseUrl:                      # authorize 跳转目标域
client_id=xxx                     # OAuth client id（各域不同：settings/accountV2）
scope=xxx                         # 通常是 grammarly.capi.all
```

同时提取环境配置对象（通常是一个 JSON.parse 模块）中的 `api` 段：

```
api: { auth, authV4Tokens, nomos, subscription, passport, vito,
       institution, payments, sso, tokens, gateway, ... }
```

这就是**攻击面地图**：每个服务名 → 完整 URL。还常包含 staging/QA 环境链（如 ppgr.io、qagr.io）——可用于对照和生产行为差异。

## 步骤 2：已登录 cookie 直通 token 链

对每个目标域重复（全用 `allow_redirects=False`）：

```
1. GET {domain}/v1/mediator/initiate（带已登录 cookie）
   → 302 Location: {authBaseUrl}/tokens/v4/api/oauth2/authorize?client_id=xxx&redirect_uri={domain}/v1/mediator/callback
2. GET authorize URL（已登录会话 → 307 直接带 code 回调，免交互）
   → 307 Location: {domain}/v1/mediator/callback?code=xxx
3. GET callback URL（完成会话绑定）
4. GET {domain}/v1/mediator/token → {"access_token": "..."}
```

注意：相对路径 Location（如 `/`）需 urljoin 处理；OAuth code 单次使用，流程失败需重新发起。

## 步骤 3：JWT payload 分析——aud 决定网关权限

解码 token 的 payload 段，看三个字段：

```
aud  = 该 token 可认证的网关列表（决定能打哪些服务）
scp  = 权限范围（如 grammarly.capi.all）
sub  = 用户 ID（同架构多域应一致——验证共享身份）
```

- 用 `aud` 含目标网关的 token 请求该网关 → 认证层放行（401 变 404 路由层）
- 之前 401 不代表不能访问——只是用错了域的 token
- 跨域验证：同一 sub 在不同域的 token 都有效 → 身份系统共享，后端可能共享数据库

## 步骤 4：错误语义分类（Fastify / Spring 两种风格）

请求到达服务后，用响应区分框架与状态：

| 响应特征 | 含义 |
|---|---|
| `FST_ERR_VALIDATION` + `anyOf const` 列表 | Fastify 校验，**枚举值全量泄露**——收集保存作合法参数 |
| `{"path":"/public/xxx"}` 404 | Spring 网关重写后的内部路由未匹配（路径带 /public/ 前缀是内部命名空间） |
| 空 body 404 | 可能是业务语义（如无组织用户查组织端点） |
| 403 `"Access denied"` / `FORBIDDEN` | 应用层授权校验生效（组织归属校验）——该对象不可越权访问 |
| 400 带字段路径（`arg0.planId`、`must be greater than 0`） | Jakarta 校验字段反推必填参数与约束 |

关键区分：**403 = 归属校验生效**（此对象不可访问）；**400 = 格式校验**（参数构造问题）；**404 = 路由/语义**（对象不存在或无组织）。三者混为一谈会误判攻击面。

## 步骤 5：框架与 SDK 识别

- Fastify 服务：错误格式 `FST_ERR_VALIDATION`，校验错误泄露 schema 约束
- Spring Boot 服务：`{"timestamp","status","error","path"}` 格式
- OpenAPI 生成 SDK：前端方法名 `xxxPost({xxxPostRequest})` / `xxxGet({...})`——方法名即端点语义；`security:[{name:"x-authorization-userId",type:"apiKey"}]` 表示服务端**期望**该 header（需实测是否信任，多数情况 JWT sub 才是身份源）

## Notes

- 所有 token 10 分钟左右过期，脚本需内嵌刷新链（重跑 4 步）而非缓存
- 请求头按前端指纹补全：X-Client-Type / X-Client-Version / x-container-id（后者可任意值，仅遥测标识）
- 优惠/折扣/实验类枚举（specialOffers 等）注入 plans 类查询通常无定价变化——服务端不信任查询参数优惠，此线低价值
- 支付类端点（subscribe）要求 Braintree nonce（支付令牌）时，无绕过手段直接关闭该线
- 已确认关闭的线要记录进项目 SUMMARY，避免重复测试
