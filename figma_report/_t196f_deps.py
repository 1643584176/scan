# -*- coding: utf-8 -*-
import io, re
js = io.open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
names = ['TrashedFilesPageView', 'TrashedFoldersPageView', 'FileBrowserPaginatedRecentFilesView',
         'PaginatedPlanAiUsageByUsersV2View', 'FileBrowserFolderPageV2View', 'LitmusBuildsListPaginated',
         'UnclaimedDomainUserView', 'AddWorkspacePinSearchFilesView', 'AdminRequestDashboardView',
         'OrgAdminUserView', 'FileBrowserPaginatedRecentFilesByEditorTypeView', 'RecentlyUsedActionsView']
for name in names:
    i = js.find('o("' + name + '",[')
    if i >= 0:
        seg = js[i:i + 260]
        m = re.match(r'o\("[^"]+",\[([^\]]*)\]', seg)
        print(f'{name}: deps=[{m.group(1) if m else "?"}]')
    else:
        print(f'{name}: NOTFOUND')
print('== sortOrder usage in args constructors (recentFiles/profile)')
for m in list(re.finditer(r'.{80}paginatedRecentFiles.{200}', js))[:8]:
    print('PRF>', repr(m.group(0))[:290])
print('DONE')
