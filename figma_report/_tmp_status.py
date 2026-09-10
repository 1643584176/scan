# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
j = json.load(open(r'D:\scan\figma_report\_r2_res_widget.json', encoding='utf-8'))
for it in j['meta']:
    print(it.get('id'), '|', it.get('name'), '|', it.get('publishing_status'), '|', it.get('publish_scope'),
          '|', it.get('content_id'), '| unpublished_at=', it.get('unpublished_at'))
