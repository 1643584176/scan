# -*- coding: utf-8 -*-
"""追加本轮(OpenAPI 清单系统挖掘)结论到 progress"""
p = r'D:\scan\netlify_report\progress-2026-09-02.md'
add = '''
## 轮次3: OpenAPI 清单系统挖掘(用户指示: 从导出的接口清单找不易发现的洞)

### 已闭环(全部安全/设计如此)
1. **全量逐方法探活**(假资源 id 无副作用法): 活路由确认(区分 JSON-404=路由活/文本-404=死)。
   副产品: POST /sites 空 body→201 直接建站(无必填校验); POST /dns_zones 空 body→500 "Name is blank"(应为400);
   POST /accounts type 枚举: team/enterprise 触发 429 deploy 限流, 其他 422; agent_runners/upload_url→403 out of credits。
2. **真实资源 GET 全量**(SITE_A): ai-gateway/providers 匿名可读(仅模型列表/env var 名, 无敏感);
   accounts/types 需认证; accounts/{id}/audit 跨账号 404 匿名 401(隔离正常);
   /services/ marketplace; database/branches 含 production 分支连接串; deploy files 列表含 sha。
3. **dns_zones**: 创建任意域名 zone 零所有权验证, 但冲突检查完整: 占用域 422(apple.com "conflicting custom domain")、
   reserved(netlify.com)、他 team 已用(google.com)、二次创建 422("already delegated to Netlify")。跨账号 404 隔离。transfer 需 account 字段。
4. **HPP 矩阵**: 所有 /sites/{id}/xxx + ?site_id=?site_slug= 覆盖: query 纯装饰, 无上下文覆盖。
5. **site name 全局唯一**: 同账号/跨账号同名创建都 422 {"subdomain":["must be unique"]}; 删除后立即释放(正常机制, 非洞)。
6. **database 家族**: ?role= 枚举仅 netlifydb_owner 有效(其余 400 "unknown role"); branches 只有 production;
   compute settings 0.25CU/sleep 300s; migrations/snapshots 空。DELETE 无确认硬删物理库(host+密码全变), POST 重建新库。
   跨账号全 401。owner 自伤面, 无越权。
7. **deploy files**: PUT 需状态非 new(错误 "deploy must be in , not new" - 状态列表为空疑似 bug);
   匿名 GET files 401、B 404。draft new 状态 DELETE 405 删不掉(残留 4 个, 预期自动过期)。
8. **hooks 家族**(关键: 字段需 data 嵌套, OpenAPI 无 schema):
   - email type: data.email 任意邮箱 201 无所有权校验(deploy 事件触发发信, spam 类低危)
   - url type: data.url 创建时 IP 黑名单校验(RFC1918/loopback/link-local/整数IP/v6映射全拒);
     0.0.0.0/userinfo/CRLF 编码可过但不可达/无影响; DNS rebinding 理论可绕(需自控域, 无法验证)
   - github_app_checks 无字段 201; slack 顶层字段 422(需 data)
9. **build_hooks**: url 参数被忽略(响应 url=api.netlify.com/build_hooks/{id}), 无回调消费, 无 SSRF。
10. **password protection**: free plan 422 "not available on this plan"。
11. **site 完整字段审计**: notification_email/jwt_secret(identity 未启用)/id_domain/has_password 等, 无未授权写面。
    SITE_A PATCH name 误改已恢复 sec-test-rcf6lz; custom_domain fuzz-up-9318.com 已清空(配额窗口过)。

### 结论
跨账号隔离/AuthZ 全部正确; 新增功能面(database/ai-gateway/dns_zones/agent_runners)校验完整。
无可提交洞。候选微发现(均不够 H1 门槛): email hook 任意邮箱、dns_zones 空 body 500、files 状态列表 bug。
残留: SITE_A 4 个 new draft deploy(无法删); A/B database 已恢复(新 host+新密码)。

### 教训
- OPTIONS "影子方法" 结论需对照 swagger 复核(database POST/DELETE 文档其实都有)
- 探活用假 id 会掩盖资源级端点; 真实资源重打一轮是必要的
- hooks 类 body 用 data 嵌套(Netlify 通知 API 风格)
'''
with open(p, 'a', encoding='utf-8') as f:
    f.write(add)
print('appended, new length:', len(open(p, encoding='utf-8').read()))
