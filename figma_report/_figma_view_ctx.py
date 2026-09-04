# -*- coding: utf-8 -*-
"""提取 livegraph view 注册上下文(args 结构),输出关键 view 详情"""
import re

d = open('D:/scan/figma_report/_js/figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()

# 高价值 view 候选(涉及他人数据面)
targets = ['ActiveAiChatThreadView', 'ActiveAiChatThreadPaginatedView',
           'ActiveFileUsersForFileView', 'OrgByIdForPlanView', 'OrgByIdForPlanUserView',
           'OrgUsersByIdView', 'TeamByIdForPlanView', 'TeamByIdForPlanUserView',
           'PageThumbnailsByFileKeyView', 'PaginatedUserAiChatThreadsView',
           'NodeAiChatThreadsBySessionView', 'MemberFlyoutInfoView',
           'MediaExportJobsForFileView', 'WorkspacePinnedFileKeysView',
           'NavigationOrgUserDataView', 'AccountTypeRequestByIdView',
           'FileMakeVersionsView', 'PlanByFileKey', 'CheckoutSessionView',
           'RepoBranchCountByIdView', 'AddWorkspacePinnedFileView']

for t in targets:
    print('=' * 20, t)
    idx = 0
    cnt = 0
    while True:
        i = d.find(t, idx)
        if i < 0 or cnt >= 2:
            break
        ctx = d[max(0, i - 250):i + 250]
        print('  @%d: ...%s...' % (i, ctx.replace('\n', ' ')[:480]))
        idx = i + 1
        cnt += 1
    print()
