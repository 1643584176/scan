# -*- coding: utf-8 -*-
"""查 bundle 中失败 view 的正确调用方式(MemberFlyout 系列、AdminRequest 系列)"""
import re

d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()

for t in ['MemberFlyoutInfoFromPlanUser', 'MemberFlyoutInfoView', 'AdminRequestDashboardRowIds',
          'SeatRequestFlyoutTeamUserView', 'UserMonetizationMetadata']:
    print('=' * 20, t)
    cnt = 0
    idx = 0
    while cnt < 3:
        i = d.find(t, idx)
        if i < 0:
            break
        print('  @%d: ...%s...' % (i, d[max(0, i - 200):i + 250].replace('\n', ' ')[:430]))
        idx = i + 1
        cnt += 1
    print()
