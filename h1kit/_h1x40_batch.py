# -*- coding: utf-8 -*-
"""h1x40: 剩余根字段匿名批量探测(用户休息轮;匿名=非参与者视角与登录态一致)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

qs = {
    'R1_resource_pub': '{ resource(url: "https://hackerone.com/reports/2487889") { __typename } }',
    'R2_docsearch': '{ search_documentation(query: "report") { __typename } }',
    'R3_application': '{ application { __typename } }',
    'R4_clusters': '{ clusters(first: 3) { total_count } }',
    'R5_assets': '{ assets(id: 92627) { total_count } }',
    'R6_mediation': '{ mediation_requests(first: 3) { total_count } }',
    'R7_tasks': '{ tasks(first: 3) { total_count } }',
    'R8_agent_guidance': '{ agent_guidance(guidance_type: "report") { __typename } }',
    'R9_cve': '{ cve_entry(cve_id: "CVE-2024-0001") { __typename } }',
    'R10_surveys': '{ surveys(first: 3) { total_count } }',
    'R11_certs': '{ certifications(first: 3) { total_count } }',
    'R12_terms': '{ terms(first: 3) { total_count } }',
    'R13_vtemplates': '{ vulnerability_templates { __typename } }',
    'R14_workflows': '{ workflow_runs(first: 3) { total_count } }',
    'R15_skills': '{ skills(first: 3) { total_count } }',
}
for k, q in qs.items():
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
        t = r.text[:350]
        print(f'{k}: [{r.status_code}] {t}')
    except Exception as e:
        print(f'{k}: ERR {e}')
