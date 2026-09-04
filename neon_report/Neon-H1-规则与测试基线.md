# Neon H1 规则与测试基线

> 项目:HackerOne neon_bbp(Neon,已被 Databricks 收购)
> 建立日期:2026-09-03(规则 2026-05/07 版)
> 状态:✅ 规则已收齐(2026-09-03)

## Scope 资产(3 项,均 Critical/Eligible)

| 资产 | 说明 | 已解决报告 |
|---|---|---|
| `https://console.neon.tech/api/v2/` | 控制面 API v2(生产) | 11 (16%) |
| `https://console.neon.tech/` | 生产控制台——**除非必要不测,测前必须邮件 bugbounty@databricks.com 联系** | 33 (48%) |
| `https://console-stage.neon.build/` | **staging 主战场**——replica of production,支持付费功能(Stripe 测试卡) | 13 (19%) |

- Open Scope:未列出的自有资产按影响也奖励
- 注册:staging 用 invite code `I-LOVE-PREVIEWS`(console-stage.neon.build/?invite=I-LOVE-PREVIEWS);**必须用 @wearehackerone.com 邮箱**

## 奖励表(CVSS 定级,90 天平均:$300 / $750 / $2,000 / $5,000)

| 级别 | CVSS | 标准 |
|---|---|---|
| Critical | 9.0–10.0 | 跨租户数据访问/污染/账号接管;**VM/容器逃逸到 K8s 节点/宿主机**;**共享存储层(Pageserver/Safekeeper)攻破**:未授权读/写/auth bypass 影响他租户;**控制面 secret/凭据提取(跨租户访问)** |
| High | 7.0–8.9 | **租户内提权到 cloud_admin/superuser/VM root**(→RCE/LFI/自己租户 token·secret 提取);单租户授权绕过;同租户沙箱逃逸 |
| Medium/Low | 按 CVSS | |

## Out of scope / 不奖励

- H1 Core Ineligible Findings;Feedback/Support/Request Private Networking 表单;测试凭据占位数据;无影响子域接管;自动化未验证报告
- **开源项目漏洞**(上游 bug 不算——平台自身集成/配置问题仍算)
- Known:CSRF、HTML injection、Invalid session termination(除非组合放大)
- 非合格:第三方未修复组件、缺 best practices、rate limiting、无 PoC 脆弱库、用户枚举
- **Lakebase 同代码库**:同一漏洞只能报一次;规则建议报 Databricks 项目(赏金更高)——提交路径决策点

## 交战规则

- **staging 为主**,生产测试先邮件 bugbounty@databricks.com 协调
- Header:`X-Bug-Bounty: xxbo`(H1 username);≤10 req/s;禁 DoS;不碰他人数据
- 测试者:H1 = hackerone.com/xxbo;H1 绑定邮箱 15652931176@163.com;H1 转发别名 xxbo@wearehackerone.com
- 账号必须 @wearehackerone.com 邮箱(非此邮箱可能被 block)
- PII 最小化,确认提权不暴露 PII

## 测试账号(待填充)

- [x] 测试标识:X-Bug-Bounty: xxbo(H1 username xxbo)
- [ ] **staging 注册中**:console-stage.neon.build/?invite=I-LOVE-PREVIEWS,邮箱 xxbo@wearehackerone.com(转发到 163)→ 待用户提供 staging cookie
- [x] 生产账号(不合规备用):libobo / org-red-waterfall-88576532 / qq 邮箱——**规则禁止直接测,仅只读确认过**
- [ ] 程序页附件 API_Calls_with_Identifiers.xlsx 清单(待用户提供)

## 攻击方向备忘(技术层,黑盒)

- 奖励表直接指向:Pageserver/Safekeeper 面、compute 逃逸、租户内 superuser 提权、控制面跨租户
- 控制面 API v2(api.neon.tech)OpenAPI 公开于 api-docs.neon.tech——先离线分析端点面
