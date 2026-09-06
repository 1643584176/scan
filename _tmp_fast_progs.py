# -*- coding: utf-8 -*-
import os
import sys

os.chdir(r'F:\scan')
sys.path.insert(0, r'F:\scan')
from h1kit import h1data

print('=== A. All open+bounty programs, eff>=70, sorted by efficiency (top 70) ===')
rows = h1data.find_programs(
    exclude=['figma', 'vercel', 'neon', 'netlify', 'supabase', 'launchdarkly',
             'wolt', 'zomato', 'box', 'signrequest', 'shopify', 'eternal',
             'mongodb', 'elastic', 'cloudflare'],
    min_efficiency=70, max_rows=70, sort_by='efficiency')
print()
print('=== B. Same but resolved time < 800h (~33d) ===')
fast = [r for r in rows if r['resolved_h'] is not None and r['resolved_h'] < 800]
for r in fast:
    print('%-30s | %-38s | eff=%-3s | 1st=%s h | res=%s h'
          % (r['name'][:29], r['handle'][:37], r['resp_eff'],
             r['first_resp_h'], r['resolved_h']))
print('TOTAL fast-resolve: %d' % len(fast))
