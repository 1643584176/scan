# store.steampowered.com 未登录测试总结(2026-08-03)

## 结论
**未登录攻击面穷尽,无漏洞。** 剩余面均需登录(购物车/愿望单/账户设置/免费游戏领取/评测)。

## 技术栈
- nginx / responsive UI / React(appstore_main.js 1916KB)/ webpack 257 chunk(manifest.js)
- CDN:store.st.dl.eccdnx.com(中国节点,URL 带 `_cdn=china_eccdnx`)
- 旧版页面用 jQuery + 服务端模板;新版页面 React + data-props 注入

## 已测并排除

| 面 | 结果 |
|---|---|
| 参数反射 cc/l/snr/utm_source/gclid/term/query/filters | 全编码(HTML 实体 / URL 编码),无 XSS |
| /search/results/ query → g_strUnfilteredURL 内联 JS 单引号字符串 | query 值 URL 编码后拼接(`%27%22%3C%3E`),无法闭合 |
| /search/ term → input value 属性 | HTML 实体编码(`&quot;&gt;`),无法闭合属性 |
| IDOR appdetails(3717370 等) | 未发布 app 受保护,success=False |
| filters 参数 ACL | 纯客户端过滤,无差异 |
| open redirect(redir 参数) | 服务器域名前缀纯字符串拼接 + login.js 三重校验(协议/前缀/`//`) |
| postMessage | CVirtualKeyboard 仅 GamepadUI;FocusRestoreReady 自指 |
| clickjacking(/login/ XFO MISSING) | CSP 有 frame-ancestors 'none',现代浏览器不可嵌 |
| /search/suggest term | 无匹配返回空,term 不反射;带 XHR 头返回空 |
| /tagdata/recommendedtags | 401(需认证) |
| /freelicense/addfreelicense/570 | 404 |
| /explore/render/、/search/hometab/TopGrossing/ | 纯数据无反射 |

## 注意
- 限流严格:高频后超时/连接关闭,恢复需 ~90s,间隔 5-6s
- /login/ 是唯一 XFO 缺失页(旧浏览器 clickjacking 面,规则排除无 well-defined risk)
- login chunk: `onComplete:e=>{e==k_PrimaryDomainFail?u(!0):window.location.assign(r)}`,redirectUrl 来自 data-props

## 结论:转目标 www.dota2.com(84 报告,现代 SSR,未登录功能多)
