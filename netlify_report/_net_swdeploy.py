# -*- coding: utf-8 -*-
"""Netlify:查 swagger 中 deploy 创建/上传相关定义"""
import yaml

sw = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
for p, methods in sw['paths'].items():
    if 'deploy' in p and ('files' in p or p.endswith('deploys') or 'deploys' in p):
        print('PATH:', p)
        for m, info in methods.items():
            if not isinstance(info, dict):
                continue
            print('  %s: %s' % (m.upper(), info.get('summary', '')))
            for prm in info.get('parameters', []):
                print('    param: %s in=%s required=%s type=%s' % (prm.get('name'), prm.get('in'), prm.get('required'), prm.get('type')))
        print()
