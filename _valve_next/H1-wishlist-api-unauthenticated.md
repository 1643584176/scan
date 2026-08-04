# H1: 未认证 API 泄露任意用户的愿望单与关注游戏列表(网页端已私密化)

> **⚠️ 判定不成立,仅供研究存档,勿提交。**
> 原因:未验证任何用户确实处于"愿望单私密"状态;gabe 为 2018 年前老账号(旧默认公开),API 返回属正常功能;网页裸 302 为功能下线特征而非权限保护(对照:games XML 走 /login/ 登录墙);新账号测试中空响应三义(不存在/为空/私密)不可区分。
> 结论日期:2026-08-03

---

## Title(标题栏)

Unauthenticated Steam Web API returns full private wishlist & followed-games data for any user (web UI treats wishlists as private — 302 to homepage)

## Severity

Low(Valve 规则:Private profile 数据 in scope,非 PII 封顶 Low)

## Asset

api.steampowered.com

## Weakness

CWE-306 Missing Authentication for Critical Function / CWE-284 Improper Access Control

---

## Description

### Summary:
`api.steampowered.com` 的 `IWishlistService/GetWishlist`、`IWishlistService/GetWishlistItemCount`、`IStoreService/GetGamesFollowed`、`IStoreService/GetGamesFollowedCount` 四个端点**无需 API key、无需任何会话认证**,即可读取**任意 steamid** 的完整愿望单(含 appid、priority、date_added)与关注游戏列表。

同时,网页端 `steamcommunity.com/wishlist/{steamid}` 与 `steamcommunity.com/wishlist/{steamid}/wishlistdata/` 对**所有用户**(包括 API 显示存在 41 项愿望单的用户)一律 `302 Moved Temporarily` 重定向到首页 —— 说明愿望单数据已被 Steam 视为私密(Steam 自 2018 年起将愿望单活动隐私默认设为私密,公开愿望单页面已移除),而 Web API 未同步实施访问控制,形成隐私绕过。

### Steps To Reproduce:

1. 未认证(无 key、无 cookie)读取任意用户完整愿望单:
   ```
   curl "https://api.steampowered.com/IWishlistService/GetWishlist/v1/?steamid=76561197960434622"
   ```
   响应 `HTTP 200`,返回 41 项完整数据(截断示例):
   ```
   {"response":{"items":[{"appid":50650,"priority":29,"date_added":1433965886},
   {"appid":215824,"priority":24,"date_added":1433965881}, ... ]}}
   ```

2. 未认证读取愿望单数量:
   ```
   curl "https://api.steampowered.com/IWishlistService/GetWishlistItemCount/v1/?steamid=76561197960434622"
   ```
   响应:`{"response":{"count":41}}`

3. 未认证读取关注游戏列表(33 个 appid):
   ```
   curl "https://api.steampowered.com/IStoreService/GetGamesFollowed/v1/?steamid=76561197960434622"
   ```
   响应:`{"response":{"appids":[211,753,765,18500,20500,39210,43110,109300,204650,210970,221410,223300,231200,232090,236430,244770,261550,282140,300550,304650,305620,316790,344740,374320,377160,414120,419270,435150,508440,578650,814380,874260]}}`

4. 网页端对照:同一用户的愿望单页面与 JSON 端点均不可见(302 → 首页):
   ```
   curl -i "https://steamcommunity.com/wishlist/76561197960434622"
   # HTTP/1.1 302 Moved Temporarily
   # Location: https://steamcommunity.com

   curl -i "https://steamcommunity.com/wishlist/76561197960434622/wishlistdata/"
   # HTTP/1.1 302 Moved Temporarily
   # Location: https://steamcommunity.com
   ```

5. 对照:用户 profile 页面正常公开可访问(非全局隐私):
   ```
   curl -s -L "https://steamcommunity.com/profiles/76561197960434622" | grep "<title>"
   # <title>Steam Community :: al</title>
   ```

6. 随机用户复验(网页 302 不可见,API 返回数据):
   ```
   curl "https://api.steampowered.com/IWishlistService/GetWishlist/v1/?steamid=76561198092420573"
   # {"response":{"items":[{"appid":1631270,"priority":0,"date_added":...}]}}  (2 项)
   curl -i "https://steamcommunity.com/wishlist/76561198092420573"   # 302 → 首页
   ```

7. 对照:无效 steamid 返回空对象(数据真实存在,非随机返回):
   ```
   curl "https://api.steampowered.com/IWishlistService/GetWishlist/v1/?steamid=99999999999999999"
   # {"response":{}}
   ```

### Supporting Material/References:
* CWE-306: Missing Authentication for Critical Function
* Valve 项目规则:Private profile 数据 in scope(非 PII 封顶 Low)
* `GetSupportedAPIList` 中该接口标记 `key=1`(文档声明需 API key),实测免 key 可访问
* Steam 隐私变更背景:SteamDB《Scanning all possible Steam IDs》确认愿望单相关隐私于 2018 年改为默认私密;2024 年起公开愿望单页面(steamcommunity.com/wishlist/{steamid})被移除,任何用户访问均被 302 至首页
* 未进行大规模枚举(仅 45 个随机 ID 抽样验证),无速率限制压力测试

---

## Impact

### Summary:
攻击者可枚举任意 steamid(从公开 profile 即可获得)未认证读取其私密愿望单与关注游戏列表,绕过 Steam 的愿望单隐私设计。

* 任意用户愿望单完整内容泄露:游戏 appid 列表、优先级、添加时间戳 —— 反映用户购买意向与兴趣
* 关注游戏列表泄露(网页端无公开展示途径)
* 无认证、无速率限制,可脚本化批量收集大量用户数据
* 网页端已按私密处理(302),API 未同步,构成设计意图绕过

---

## 备注(提交前自查)

- [ ] 严重度:符合"Private profile 数据 in scope (非 PII 封顶 Low)" → Low
- [ ] 数据非 PII(愿望单游戏列表),不涉及联系方式等
- [ ] 抽样 45 个随机 steamid 验证一致性,未做大范围枚举(遵守规则)
- [ ] 若 Valve 回复 "by design"(愿望单 API 一直公开),需准备 302 行为对照作为反驳
- [ ] 可选增强:用 Wayback Machine 验证 2024 年前网页 wishlist 曾 200 返回(证明行为变更)
