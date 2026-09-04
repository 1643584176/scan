# -*- coding: utf-8 -*-
import yaml, json
sw = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
d = sw['definitions']['deploy']
print(json.dumps(d, indent=1))
