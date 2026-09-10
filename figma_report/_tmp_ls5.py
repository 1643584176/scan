# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_sq1_map.txt', encoding='utf-8').read().splitlines()
targets = ('fonts', 'plugins', 'plugin_runs', 'items', 'resource', 'resource_uses', 'libraries', 'styles',
           'versions', 'recent_prototypes', 'viewer_restricted_draft', 'folder_join_link', 'file_diff',
           'resource_scope_settings', 'voice', 'storybook', 'sgs_debug', 'form_post', 'extension_analytics',
           'page_status_options', 'plan_promo', 'policy_configs', 'resource_saves', 'resource_connection',
           'resource_connection_invite', 'roles', 'templates', 'try', 'internal', 'workspace_approved_library',
           'org_approved_library', 'user_notifications_bell', 'state_group_log_data', 'variable_set_log_data',
           'variable_log_data', 'component_log_data', 'buzz_approvals', 'curator', 'assistant', 'arkose', 'ip_check')
cur = None
mode = None
for l in t:
    if l.startswith('====='):
        mode = l
        continue
    m = re.match(r'^-- ([a-z_0-9]+) \((\d+)\) --', l)
    if m:
        cur = m.group(1)
        if cur in targets and '未深测' in (mode or ''):
            print(f'-- {cur} --')
        continue
    if cur in targets and l.strip().startswith('/') and '未深测' in (mode or ''):
        print('  ' + l.strip())
print()
# search 关键字全图扫描
print('== 含 search/font/export 的端点 ==')
for l in t:
    if re.search(r'(search|font|export)', l) and l.strip().startswith('/'):
        print('  ' + l.strip())
