# -*- coding: utf-8 -*-
"""提取 swagger 中新 database 端点 + ai-gateway 的完整定义"""
import re

data = open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8', errors='ignore').read()

targets = ['/sites/{site_id}/database/migrations', '/sites/{site_id}/database/branch/{branch_id}/reset',
           '/sites/{site_id}/database/snapshot/{snapshot_id}',
           '/sites/{site_id}/ai-gateway/token', '/accounts/{account_id}/ai-gateway/token']

lines = data.split('\n')
for t in targets:
    for i, ln in enumerate(lines):
        if ln.strip().startswith(t + ':') or ln.strip() == t + ':':
            # 向后打印直到下一个顶级路径(两空格缩进的路径)
            print('=' * 20, t, '=' * 20)
            j = i
            while j < len(lines) and j < i + 80:
                print(lines[j])
                if j > i and re.match(r'^  /[A-Za-z0-9_{}./\-]+:', lines[j]):
                    break
                j += 1
            print()
            break
