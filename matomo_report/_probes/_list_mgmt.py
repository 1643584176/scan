# -*- coding: utf-8 -*-
"""List no-check methods that are NOT report/archive-backed (management/config classes),
grouped by plugin, so matrix can run without archived data."""
import json
import re

d = json.load(open('_nocheck_methods.json', encoding='utf-8'))
callable_ = [x for x in d if not x['method'].startswith('_')]

# plugins whose methods read log/archive data (need seed+archive)
REPORT_PLUGINS = {'Contents', 'CustomDimensions', 'DevicePlugins', 'DevicesDetection',
                  'Events', 'Goals', 'Referrers', 'Resolution', 'Transitions',
                  'UserCountry', 'UserLanguage', 'VisitorInterest', 'VisitsSummary',
                  'VisitTime', 'Actions'}

mgmt = [x for x in callable_ if x['file'].split('\\')[-2] not in REPORT_PLUGINS]
print('management/other methods:', len(mgmt))
from collections import Counter
print(Counter(x['file'].split('\\')[-2] for x in mgmt))

WRITE = re.compile(r'^(add|update|delete|create|enable|disable|change|pause|resume|export|import|unlink|link|set|remove|clear)\w*')
for x in sorted(mgmt, key=lambda y: (y['file'].split('\\')[-2], y['method'])):
    kind = 'WRITE' if WRITE.match(x['method']) else 'read'
    print('%-4s %-22s %-45s %s' % (kind, x['file'].split('\\')[-2], x['method'], x['params'][:80]))
