# -*- coding: utf-8 -*-
import json
s = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
print(json.dumps(s['components']['schemas']['BucketCreateRequest'], indent=1))
