# LaunchDarkly Bugcrowd 项目规则与测试基线

> 数据来源:Bugcrowd engagement 页面(用户 2026-09-02 提供)
> 用途:测试前基线、报告判定依据、查重参考

## 1. 项目概况

- 平台:Bugcrowd(Managed Bug Bounty,原 HackerOne 项目已迁移)
- 目标:LaunchDarkly(功能开关/Feature Management SaaS)
- 状态:进行中,2026-05-19 开始
- 验证:10 天内 75% 接受或拒绝
- 平均 payout:$1,386.84(近 3 个月),已奖励 42 个漏洞

## 2. 奖励结构

| 级别 | 金额 |
|---|---|
| P1 | $6500 – $7500 |
| P2 | $2500 |
| P3 | $1250 |
| P4 | $150 |

- 按 CVSS 定级,可能因 likelihood/impact 调整(降级必须提供解释+可申诉)

## 3. In Scope 目标

| 目标 | 说明 | 技术标签 |
|---|---|---|
| app.launchdarkly.com | 主应用(登录、flag/context/segment 管理;admin 管理 org 用户/角色/环境) | ReactJS, PostgreSQL, Elasticsearch |
| app.launchdarkly.com/api/v2/ | 后端 API;`/api/v2/` 和 `/internal/` 需 ldso session cookie 或 Authorization token;**`/private/` 用独立认证机制,非 LD 用户不应可访问——任何不当可访问都值得报告** | |
| LaunchDarkly SDKs | 开源(-sdk 后缀 repo);SDK 与服务器通信;handler 逻辑漏洞 | Java, Rust, Haskell |
| stream.launchdarkly.com | Streamer:SDK flag 数据流(client/server) | Go, AWS |
| events.launchdarkly.com | Event Recorder:SDK 事件采集 | Go, AWS, Elasticsearch |
| docs.launchdarkly.com | 文档站:搜索栏 XSS/injection;跨域请求 app 的 CSRF | |

## 4. Out of Scope

blog.launchdarkly.com、launchdarkly.com、sandbox.launchdarkly.com、slack.launchdarkly.com、status.launchdarkly.com、launchdarkly.atlassian.net;未列出的任何子域

- 发现 OOS 目标漏洞可报告但**无奖励**

## 5. Focus Areas(重点方向)

- app:不当认证/访问控制、角色定义外的权限提升、用户输入 XSS/SSRF
- **Custom Contexts(新 GA)**:用户模型升级为自定义 contexts(users→devices/business units/orgs),关注新基础设施/UI 组件的 web 漏洞与业务逻辑错误
- **Experimentation(2022 刷新)**:实验创建与运行的漏洞/逻辑错误
- api/v2:未认证/未授权 API 访问、跨账号/跨环境意外数据、handler 逻辑错误导致未定义行为
- SDK:flag 评估逻辑;客户端 SDK 不应暴露 flag 规则,任何不当暴露值得注意
- stream:攻击者利用 flag 评估逻辑不当获取他人 flag 信息
- events:事件记录机制利用
- docs:搜索栏 XSS/injection;跨域请求 CSRF

## 6. Known Issue(不奖励)

- 账号验证与忘记密码页面的限流

## 7. Excluded Submission Types(完整排除)

- 支持团队接口(生成邮件/工单/通知的 chat bot、表单)
- 第三方集成与端点(未来开放)
- DoS/DDoS、限流绕过、邮件轰炸
- 一切社工
- 无敏感操作页面的 clickjacking
- 未认证表单或无敏感操作表单的 CSRF
- 需 MITM 或物理设备访问
- 已知漏洞库无工作 PoC
- CSV 注入(无平台特定漏洞)
- SSL/TLS 配置缺失最佳实践
- 非认证端点限流/爆破
- CSP 缺失
- HttpOnly/Secure 缺失(除 **ldso cookie** —— ldso cookie 的 flag 缺失可报!)
- 邮件 SPF/DKIM/DMARC
- 旧浏览器(落后 2 个稳定版)
- 浏览器扩展导致的 open redirect
- 版本披露/banner/描述性错误消息/堆栈
- Tabnabbing
- Open redirect(除非额外安全影响)
- 需要不可能用户交互
- 非 -sdk 后缀 repo
- 源码依赖扫描结果
- 客户端 SDK key 可见性(设计公开)
- 网站公开客户端 key(Algolia、TrackJS 等)
- Jira ServiceDesk 公开注册
- 验证邮件收件箱垃圾
- 应用内/邮件 HTML 注入
- 密码重置链接不因邮箱变更过期
- 开源 repo 扫描
- P5

## 8. 测试约束

- 账号必须用 @bugcrowdninja 邮箱(或含 bugcrowd 子串,如 name+bugcrowd1234@example.com)
- SSRF(含 webhook SSRF)必须有到达证明+元数据
- 发现可能导致 post-exploitation(修改/删除数据)的漏洞:**停止测试直接提交**
- 生产环境测试;禁止碰其他用户数据、删除/编辑站点、DoS
- 多路径/多端点/多参数重复视为重复(跨 dev/staging/prod 同根因也重复)
- 报告必须含:测试角色、问题解释、安全影响、详细复现步骤
- 一个报告一个漏洞(链式利用除外,须说明关联)

## 9. 测试约束提炼(规则 → 方法)

1. **最高优先级:/private/ API 未授权访问**(官方明确点名"不当可访问值得报告")
2. **Custom Contexts 新基础设施**(新代码,撞车少,官方点名关注)
3. 访问控制:跨账号/跨环境数据(API v2 + internal)
4. 权限提升:角色定义外操作(admin 管理面)
5. 客户端 SDK flag 规则暴露(streamer)
6. events 事件记录机制
7. ldso cookie 的 HttpOnly/Secure 缺失(唯一豁免的 cookie)
8. 不做:扫描器轰炸、限流绕过、社工、第三方集成

## 10. 账号与凭据(本地专用,禁止提交 git)

- [ ] 待注册:@bugcrowdninja 邮箱测试账号(用户操作)
- [ ] 注册后保存 ldso session cookie 与 access token
