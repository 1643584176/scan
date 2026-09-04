# -*- coding: utf-8 -*-
"""追加 custom_domain 面结论到 progress"""
txt = r'''

### PATCH /api/v1/sites/{id} 字段级攻击 —— 关闭(mass assignment 面打穿)
- 顶层白名单: name/custom_domain/processing_settings 有效; account_id/account_slug/team_id/state/plan/ssl/user_id/role/未知字段 全部 200 但服务端忽略(响应回显原值)
- custom_domain 无 DNS/所有权验证, PATCH 即 200 并持久(证书 provisioning 失败不自动回滚, url/ssl_url 被改写)
- custom_domain 配额: 账号级 3 次/小时("3 times per hour on this plan"), 非 per-site
- custom_domain 唯一性: 按注册域全局唯一; 冲突 422 错误消息泄露占用者 site_id: "must be unique (域名, site_id)" —— 占用者 site 跨账号 GET 404(信息泄露低危无后续)
- example.com 家族全冲突(占主 a0adc15c-3f90-49a8-acb4-3ec6d1e19e3c, 推测注册域级唯一)
- 绑定后证书 provisioning 期间不能改 cd("We're provisioning a certificate for"); 删站即释放域名
- 嵌套: build_settings.env -> 400 "new environment variables experience"(隔离到新 API); cmd/stop_builds 接受; plugins 数组可注入任意包(构建时执行, 仅影响自己站, 需 repo 集成触发); processing_settings 字段级过滤
- 结论: 服务端字段白名单严密; 唯一异常 = custom_domain 无验证占用(域名抢占 = DoS 类 OOS) + 冲突错误 site_id 泄露(低危) -> 无可报洞, 关闭
- 待清理: SITE_A custom_domain 残留 fuzz-up-9318.com(cd 配额 3/h 锁, 等窗口恢复后 PATCH null 清空, 站点 name 恢复 sec-test-rcf6lz)
'''
with open(r'D:\scan\netlify_report\progress-2026-09-02.md', 'a', encoding='utf-8') as f:
    f.write(txt)
print('appended')
