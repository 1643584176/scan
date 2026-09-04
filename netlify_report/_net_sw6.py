# -*- coding: utf-8 -*-
import yaml, json
sw = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
print(json.dumps(sw['definitions']['deployFiles'], indent=1))
