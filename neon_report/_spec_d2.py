# -*- coding: utf-8 -*-
"""离线:NeonAuthSupportedAuthProvider / email_server / webhook 描述细节"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comp = spec['components']['schemas']

for n in ['NeonAuthSupportedAuthProvider', 'NeonAuthEmailServerConfig', 'NeonAuthWebhookConfig',
          'DataAPISettings', 'EnableNeonAuthIntegrationRequest']:
    sch = comp.get(n)
    print('==', n)
    if not sch:
        continue
    print('  desc:', sch.get('description', '')[:300])
    if sch.get('enum'):
        print('  enum:', sch['enum'])
    if sch.get('type') == 'array':
        print('  items:', sch.get('items'))
    for k, v in sch.get('properties', {}).items():
        d = v.get('description', '')
        print('   %s: %s | %s' % (k, v.get('type'), d[:200]))
        if v.get('enum'):
            print('       enum:', v['enum'])
    # 找 examples / default
    for k, v in sch.get('properties', {}).items():
        if 'default' in v:
            print('   default %s = %s' % (k, v['default']))
        if 'example' in v:
            print('   example %s = %s' % (k, v['example']))
