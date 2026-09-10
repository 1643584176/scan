# -*- coding: utf-8 -*-
import json
hs = json.load(open('D:/scan/h1kit/_h1x148_handles.json', encoding='utf-8'))
print('total:', len(hs))
print(hs[:20])
