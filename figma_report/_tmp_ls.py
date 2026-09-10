# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_sq1_map.txt', encoding='utf-8', errors='replace').read()

show_doms = ['file', 'session', 'spell-check-words', 'team_join_link', 'invites',
             'user_notifications', 'user_sidebar_sections', 'feed_posts', 'feed_visited',
             'follows', 'followers', 'following', 'pinned_files', 'profile', 'multiplayer',
             'community', 'tagged_file', 'guidelines', 'password', 'upnode', 'voice']
blocks = re.split(r'\n-- ', t)
for b in blocks:
    m = re.match(r'([a-z_0-9/.-]+) \((\d+)\) --', b)
    if m and m.group(1) in show_doms:
        print(f'-- {b[:1200]}')
        print()
