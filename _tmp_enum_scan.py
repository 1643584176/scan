import re

p = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/42dcb5db/42dcb5db.jsonl'
raw = open(p, encoding='utf-8').read()

# find the V3 result with enumValues for AnalyticsFromEnum (a list of names)
# search for 'amazon_aws_abstract_findings'
idxs = [m.start() for m in re.finditer(r'amazon_aws_abstract_findings', raw)]
print('occurrences:', len(idxs))
for i in idxs[:4]:
    seg = raw[max(0,i-1500):i+2500]
    print('----- @', i)
    print(seg.replace('\\n', '\n')[:4000])
    print()
