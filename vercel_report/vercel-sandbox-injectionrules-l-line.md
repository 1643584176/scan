# L 线（injectionRules 头注入面）测试结论归档（2026-08-30）

> 窗口剩余：08-30 ~ 09-01（2 天）| 脚本：_x_n30.py ~ _x_n37.py（输出 _x_n3*_out.txt）
> 结论：**无提交价值**，该面关闭（不满足 D 线三主证，无跨租户影响）。仅记录可复用结论供组合面使用。

## 一、注入能力（已确认生效）

| 头 | 结果 | 备注 |
|---|---|---|
| 任意自定义头 | ✅ 注入到 allowedDomains 内任意域 | n30: httpbin.org 收到 `X-T: 1`/`X-Test-2: abc`；Vercel 资产同样生效 |
| `Authorization: Bearer FAKE123` | ✅ 注入成功 | n34: echo 回显 `authorization: Bearer FAKE123` |
| `x-api-key` / `X-API-KEY` / `Api-Key` | ✅ 全大小写变体均可注入 | n32/n35 |
| `x-vercel-proxy-secret` / `X-VERCEL-PROXY-SECRET` | ✅ 任意大小写注入成功 | n34/n35 |
| env（创建时注入 `FOO=bar`） | ✅ guest 内生效 | n30 |
| OIDC token 自动注入 | ✅ custom 模式对 allowedDomains 请求自动带真实 token | n32③/n36③（无需 injectionRules 声明） |

## 二、平台保护（不可绕过，安全设计）

| 头 | 结果 |
|---|---|
| `x-vercel-oidc-token`（注入 FAKE） | ❌ 被真实 token 覆盖；大小写变体（`X-VERCEL-OIDC-TOKEN`/`X-Vercel-OIDC-Token`）同样被覆盖 |
| `x-vercel-proxy-signature`（注入 FAKE） | ❌ 被真实签名覆盖；大小写变体同样被覆盖 |
| `Host`（注入 vercel.com） | ❌ 被强制覆盖为真实目标域 |
| `X-Forwarded-For` / `X-Real-IP` / `X-Vercel-Forwarded-For` | ❌ IP 链由平台生成，注入值不保留 |
| CRLF 注入（值含 `\r\n`） | ❌ API 400 拒绝（"header value ... is invalid"） |
| 多值头（数组值） | ❌ API 400 拒绝（"should be string"） |

**结论**：Vercel 对平台保留头的覆盖是大小写不敏感的精确匹配 → 签名/OIDC 伪造不可行。

## 三、域格式边界

| 配置 | 结果 |
|---|---|
| `allowedDomains: []` + injectionRules | 创建 200，但注入规则不隐式放行域（curl EXIT=6 DNS 解析被拦） |
| `allowedDomains: ["169.254.169.254"]` / `["100.64.0.1"]` | API 接受（创建 200），但连接仍被拦（curl EXIT=56）→ IP 格式接受但策略层不放行 |
| `allowedDomains: ["*.vercel.app"]` | **API 接受且生效** → 可访问任意 vercel.app 部署（含 OIDC 自动注入） |
| 注：IP 与通配符的"放行"语义是否与文档一致待查（无安全影响：均为 owner 显式配置） | |

## 四、管理面缺陷（发现但判定 Low/无提交价值）

1. **readback 不回显 injectionRules**：创建后 GET 只回 `mode`+`allowedDomains`，injectionRules 不可见（n30/n36f）
2. **PATCH /v2/sandboxes/{name}?projectId= 对 networkPolicy 部分生效**：
   - `allowedDomains` 更新 ✅ 生效（n36g: echo → httpbin.org）
   - `injectionRules` 更新 ❌ 静默忽略（n36h: X-Orig→X-Dyn 不生效；n37: 移除也不生效，原规则保留）
   - 语义 = merge（忽略 inj 字段），返回 200 无任何错误提示 → 配置承诺与实际行为偏差
3. PATCH 不接受 `name` 字段（400 additional property）

**判定**：同类于 env PATCH 静默忽略 pitfall；影响仅限沙箱 owner 自身配置漂移，无跨租户/隔离影响 → 不提交。

## 五、组合面提示（后续若出现配置 IDOR 时可复用）

- injectionRules 头注入能力 + 配置修改越权 = 向受害者 allowedDomains 注入任意头（Authorization/x-vercel-proxy-secret）
- `*.vercel.app` 通配符 + OIDC 自动注入 = 以项目身份访问任意 vercel.app 部署（aud 固定，需下游信任链）
- 平台保留头不可伪造 → 下游若依赖 x-vercel-proxy-signature/OIDC 做鉴权是安全的（除非下游解析错误）

## 六、残留沙箱核查

- 全部测试沙箱已删除（l30-l37 系列）；429 为创建频率限流（等待 60-90s 恢复），非并发占用
