# Uber 侦察状态（2026-08-06 保存，明天继续）

## 已确认的攻击面

### 1. m.uber.com/go/graphql（Apollo GraphQL，匿名可调）
- headers: `x-csrf-token: x`（固定值）+ `x-uber-rv-initial-load-city-id: 2715` + `x-uber-rv-session-type: desktop_session` + `x-uber-client-name: web-plan` + 浏览器 cookie（jwt-session）
- POST JSON body: `{operationName, variables, query}`，完整 query 文本可执行（非 APQ）
- introspection 硬关闭；`_service` 报 Invalid GraphQL query；`_entities` 不存在（非 federation）
- **错误 oracle**：`something went wrong`=字段不存在；`Invalid GraphQL query`=字段存在但缺参数；`unauthorized`=执行层拒绝
- 已提取 13 查询 + 11 fragment → `_uber_queries_full2.json`（展开脚本 `_uber_expand_frags2.py`，注意保留换行去注释，v1 有 `# deprecated` 注释压缩 bug）
- **匿名可用（返回数据）**：PudoAutocompleteBase / PudoLocationSearch / PudoResolveLocation / PudoResolveLocationPudoFragment / PudoResolveInitialParams（均为地点数据）
- **需登录**：PudoFlights / PudoResolveFlight / SavedPlaces / PudoLocationRefinement / PudoCitySearch / WayfindingInstructions
- **隐藏根字段（存在但参数未知，全报 Invalid GraphQL query）**：userInfo / currentUserProfile / userProfile / stores / estimates / favorites / remoteConfig / countries / currencies / contact
- currentUser 匿名 → UNAUTHENTICATED（字段确认存在）

### 2. www.uber.com/api/{op}（fusion RPC 桥接，匿名可调）
- POST + `x-csrf-token: x` + cookie，body 为参数 JSON
- 从 JS 提取操作名：`_uber_w_ops_exact.json`（精确模式），全部测试结果 `_uber_www_ops_out.txt`
- **匿名可用（公开数据）**：getCitySearch / loadPlaceDetails / loadPlaceDetailsByCoordinates / loadSuggestions / getSupportedLocales / loadDriverGuarantee / getProductSuggestions / getMapHeroEnabledProducts 等
- **需登录（User uuid not found）**：getUserPersonalizedData / getUberCashBalance / getUserRating / getMembershipAttributes / getUpcomingActivities / getPromoPill
- **getPesData 参数链（未打通）**：cityId ✓ → aggregateType（合法值 WEEKLY/MONTHLY/DAILY）✓ → uberServiceType ✗（试过字符串全挂，**可能是数字 ID，明天试 0-50**）。返回字段含 percentileAssociatedSupplyHours（司机收入百分位，城市级聚合数据，价值存疑，可能是 Uber 公开的 earnings 数据）
- 错误响应泄露内部源码路径（/home/udocker/uber-sites/...）→ Informational，不报

### 3. m.uber.com 自己的 RPC（未找到桥接路径）
- JS 里有 getHomeScreenLayout / getOfferDetails / getRankedOffers（fusion-plugin-rpc）
- `/api/` 404、`/_api/` 404 → apiPath 配置未找到，可能在别的 chunk
- getOfferDetails/getRankedOffers 前端 enabled 依赖 isLoggedIn（登录才发）

## 待办（明天优先级）
1. getPesData `uberServiceType` 数字枚举（0-50），打通看返回是否只是公开数据
2. 找 m.uber.com RPC apiPath（搜 bootstrap.json / runtime config，或抓真实网络请求）
3. 隐藏 GraphQL 字段参数：从 auth.uber.com / apps 其他前端 JS 找 userInfo/stores/estimates 的调用定义
4. m.uber.com 其他页面（/go/looking、/go/booking、/go/reserve）抓 JS，可能含更多查询
5. auth.uber.com JS：认证 mutation（注册/验证码/密码重置未认证链）

## 关键文件
- 查询提取/测试：`_uber_extract_gql2.py` / `_uber_expand_frags2.py` / `_uber_test_all.py` / `_uber_enum_fields.py`
- m.uber.com JS：`js_m/`（40 个）；www.uber.com JS：`js_w/`（94 个）
- cookies 快照：`_uber_www_cookies.json`
- 查询数据：`_uber_queries_full2.json` / `_uber_w_ops_exact.json`
- 测试输出：`_uber_www_ops_out.txt` / `_uber_enum_out.txt`
- 侦察脚本：`_uber_probe.py` / `_uber_csrf.py` / `_uber_www_probe.py` / `_uber_www_api_probe.py` / `_uber_www_test_ops.py`
