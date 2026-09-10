# -*- coding: utf-8 -*-
"""h1x53e: bundle 考古 intake_workflow/workflow_runs/WorkflowRun/ReportAssistantConversation 前端调用形态"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

for pat in ['intake_workflow', 'workflow_runs', 'WorkflowRun', 'workflow_step_runs', 'high_priority_summary',
            'ReportAssistantConversation', 'conversation(', 'pentest_report', 'extracted_report_data', 'ExtractedReportData']:
    hits = list(re.finditer(re.escape(pat), t))
    print(f'### {pat}: {len(hits)} hits')
    for m in hits[:5]:
        j = m.start()
        print('--- @', j)
        print(t[max(0, j-250):j+350].replace('\n', ' ')[:600])
        print()
