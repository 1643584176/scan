# -*- coding: utf-8 -*-
"""解析 swagger.yml, 输出全量 path+method 并按非常规洞型分类"""
import yaml, json, re, sys

with open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8') as f:
    spec = yaml.safe_load(f)

paths = spec.get('paths', {})
print('total paths:', len(paths))

# 全量输出到文件
out = []
for p, item in paths.items():
    for m, op in item.items():
        if m not in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options'):
            continue
        summ = (op.get('summary') or '')[:60]
        # 参数摘要
        params = []
        for prm in op.get('parameters', []) or []:
            if prm.get('in') == 'path':
                params.append('{%s}' % prm.get('name'))
        params = ' '.join(params)
        out.append('%-7s %-90s %s | %s' % (m.upper(), p, params, summ))

with open(r'D:\scan\netlify_report\_openapi_endpoints.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print('total ops:', len(out))

# 洞型关键词分类
cats = {
    'lock/unlock/状态转换':   r'(lock|unlock|rollback|restore|archive|transfer|lock_deploys|unlock_deploys|traffic)',
    'token/密钥/凭证':        r'(token|key|secret|credential|password|session|jwt)',
    'webhook/hook/回调':      r'(hook|webhook|callback|trigger|submission)',
    '成员/角色/邀请':         r'(member|role|invite|pending|guest|collaborator)',
    '批量/bulk':              r'(bulk|batch|all\b)',
    '审计/日志/事件':          r'(audit|log|event|traffic|analytics)',
    '部署/发布控制':           r'(deploy|publish|release|rollback|lock)',
    'DNS/域名/证书':          r'(dns|domain|certificate|ssl)',
    '支付/账单/plan':         r'(payment|billing|invoice|plan|charge|customer)',
    '函数/边缘':              r'(function|edge|runtime)',
    '插件/snippet/注入':      r'(plugin|snippet|injection|header|redirect)',
    '搜索/查询/导出':          r'(search|query|export|download)',
    '表单/数据提交':           r'(form|submission|file|upload)',
    '账户/用户设置':           r'(user|account|profile|avatar|oauth|connected)',
}
print()
for cat, rx in cats.items():
    hits = [l for l in out if re.search(rx, l, re.I)]
    print('%-24s %3d' % (cat, len(hits)))
    for h in hits[:8]:
        print('   ', h)
    print()
