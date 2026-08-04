# www.dota2.com 未登录测试总结(2026-08-03)

## 结论
**未登录攻击面穷尽,无漏洞。** 纯 React SPA(webpack,245 chunk)+ JSON API,反射/注入面全部关闭。剩余面均需登录(观战收藏、spoiler block、战队收藏、BP 购买)。

## 技术栈
- nginx / React 17 SPA(`#dota_react_root`)/ webpack manifest+main(2MB)+libraries(1.9MB)
- CDN:china_eccdnx;XFO SAMEORIGIN;**无 CSP、无 HSTS**;sessionid cookie(Secure+SameSite=None,anti-CSRF)
- 服务端仅渲染 title(newsentry/patches 动态,内容来自 store events 后台数据)
- `#application_config data-config` 注入服务端配置(EUNIVERSE/CDN URL 等,固定值)

## API 端点
### /datafeed/*(9 个,全部公开 JSON)
| 端点 | 参数 | 结果 |
|---|---|---|
| herolist / herodata | language, hero_id | language 白名单(非法→status:8);hero_id atoi 前缀解析(`1'`→1),**无 SQLi**(`1 AND 1=2` 仍返回);无隐藏英雄(125-160 全部已发布) |
| itemlist / itemdata / abilitylist / abilitydata | language, *_id | desc_loc 含 HTML 但前端 React children 文本渲染,非 innerHTML |
| patchnoteslist / patchnotes | language, version | version 无效→`message` JSON 内反射,无 HTML 上下文 |
| neutralitems | language, hero_type, tier | 正常 |
| CORS | - | 无 ACAO,不反射 Origin |
| JSONP | - | callback 参数无效 |

### /react/*(观战/BP 系统)
- getbpprices(item_defs)→ 空数组(活动过期/需正确参数)
- getwatchedgames/getspoilerblock/getfavoriteteams/getlivestreams → 空或 [] 
- setwatchedgame/setspoilerblock/togglefavoriteteam → 需登录(setspoilerblock 明确 "not logged in")
- login_mobile_auth/steam_spinner → SPA 外壳

### 其他
- /ingest POST → 200 空(遥测)
- store.steampowered.com/events/ajaxgetpartnereventspageable?appid=570&origin=...(首页数据源)→ 公开 JSON,origin 参数无影响,无 CORS

## 反射测试
- SPA 路由(/newsentry/:gid、/patches/:ver、/dotaplustester/:id/:key、/templatepage、/crownfall、/?q=、/home?l=、#fragment)→ **全部无 DOM 反射**(Playwright 渲染验证)
- /patches/任意版本 → 回退显示最新 7.41e

## 注意
- Playwright 修复:Windows 下 `proxy={"server":"direct://"}` 会转成 `--proxy-server=http://direct` 导致 ERR_PROXY_CONNECTION_FAILED;必须用 `args=["--no-proxy-server"]` + 去掉 proxy 参数
- SPA 抓包用 `wait_until="domcontentloaded"` + sleep(networkidle 永不空闲)
- dota2 JS 内部泄漏 `https://confluence.valve.org/display/DOTA/...`(内部 Confluence,非漏洞)

## 结论:转目标 steamcommunity.com(Valve 最大未登录读取面)
