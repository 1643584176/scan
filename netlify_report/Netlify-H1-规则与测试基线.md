# Netlify HackerOne 规则与测试基线

来源:用户粘贴 hackerone.com/netlify(2026-09-02)

## 奖励
- Low: 平均 $200(37.77% 报告)
- Medium: 平均 $500(37.77%)
- High: 平均 $2,500(16.49%)
- Critical: 平均 n/a(7.98%),整体范围 $200-$6,000
- CVSS 定级,Netlify 酌情决定

## 测试范围(硬性)
1. **只能测自己拥有的账号**
2. **必须用 HackerOne email alias 注册**(username@wearehackerone.com)→ 有资格领赏金
3. **允许创建多测试账号**:username+netlify@wearehackerone.com(加号法)→ 官方推荐用于测不同攻击向量/权限级别
4. 端点地图(官方):https://hackerone-endpoint-map.netlify.app/endpoint-map.png
   - 程序范围比地图更广;地图列出值得关注的子域

## In-scope 关注点(从攻击面描述)
- app.netlify.com(UI)
- api.netlify.com(API)
- 构建系统(Git push 触发)
- CDN(静态+动态内容托管)
- 环境变量 / GraphQL 第三方 API 联盟 / 构建集成 / DNS 管理 / analytics / log drains / 站点认证 / forms

## Out of Scope
- 非自己拥有的客户账号测试(明确禁止)
- 使用 Netlify 的第三方网站(客户站点)
- 对公开 GitHub repo 开 PR
- 无敏感操作的 Clickjacking
- 未认证/登出/登录 CSRF
- MITM / 物理访问
- 已知脆弱库且无 PoC
- CSV 注入(无漏洞演示)
- SSL/TLS 配置最佳实践缺失
- DoS(含域名/子域名劫持)
- 无攻击向量的 Content spoofing / 文本注入
- 密码重置端点限速缺失
- 密码重置后强制登录缺失
- Avatar 文件上传(除非端到端证实影响且读过程序范围)
- **自己站点构建中的 reverse shell / RCE**——例外(in-scope):
  - 提权到 root
  - 获取用户本不可访问的敏感 secrets
  - 容器逃逸
  - 访问编排控制面
- Core Ineligible Findings(H1 标准列表, 内容未随贴提供)

## 报告要求
- 详细可复现步骤;一个报告一个漏洞(链式可合并)
- 禁止社工;良好努力避免隐私侵犯/数据破坏/服务中断
- 只与自有账号交互;如检索到客户 PII 需立即报告
- 响应:首响 5 工作日 / triage 10 工作日 / 赏金 5 工作日

## 对当前测试的含义
1. **当前测试账号(1643584176@qq.com)不是 H1 alias** → 发现的漏洞若要领赏金,需用 H1 alias 账号(或 +netlify 变体)复现验证
2. **database-query 越权验证被规则明确支持**:用第二个自有账号(username+netlify@wearehackerone.com)对测 → 允许(测不同权限级别)
3. **构建 RCE 例外面是重点**:自站构建内 RCE 本身 OOS,但 root 提权/敏感 secret/容器逃逸/编排控制面 in-scope → 与 Vercel 沙箱方向一致
4. 第三网站 OOS → 不要在客户站点(.netlify.app 非自有)上测试
5. **高价值方向排序**:
   - database-query 跨账号越权(自有两账号, 中-高危, SQL 执行)
   - 构建/函数沙箱逃逸、编排控制面访问(严重级, 但难度高)
   - GraphQL 联盟(第三方 API federation)权限面
   - 环境变量/log drains/站点认证配置面

## 待办
- [ ] 抓官方端点地图(hackerone-endpoint-map.netlify.app/endpoint-map.png)
- [ ] 用户注册 H1 alias 账号(username+netlify@wearehackerone.com)或直接用 H1 alias 注册新账号
- [ ] 越权对测 database-query
