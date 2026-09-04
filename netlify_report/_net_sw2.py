# -*- coding: utf-8 -*-
import yaml, json
sw = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
names = [k for k in sw['definitions'] if 'eploy' in k]
print(names)
d = sw['definitions'].get('Deploy') or sw['definitions'].get(names[0])
print(json.dumps(d, indent=1)[:2000])
