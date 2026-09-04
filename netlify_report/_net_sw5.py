# -*- coding: utf-8 -*-
import yaml, json
sw = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
p = sw['paths']['/sites/{site_id}/deploys']
print(json.dumps(p['post'], indent=1)[:2500])
