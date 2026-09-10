# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_sq1_map.txt', encoding='utf-8').read().splitlines()
targets = ('file', 'community', 'upnode', 'multiplayer', 'session', 'team_join_link', 'user_notifications', 'user_sidebar_sections', 'pinned_files', 'invites', 'profile', 'followers')
cur = None
for i, l in enumerate(t):
    m = re.match(r'^-- ([a-z_]+) \(', l)
    if m:
        cur = m.group(1)
        if cur in targets:
            print(f'== {cur} ==')
        continue
    if cur in targets and l.strip().startswith('/'):
        print('  ' + l.strip())
