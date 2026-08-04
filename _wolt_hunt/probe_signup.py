# -*- coding: utf-8 -*-
"""从 checkout 页点 Sign up 看注册表单"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

SHOT = 'D:/scan/_wolt_hunt/_payment_shots'
os.makedirs(SHOT, exist_ok=True)

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
    ctx = br.new_context(viewport={'width': 1440, 'height': 900}, locale='en-US')
    page = ctx.new_page()
    
    # 导航到首页（先触发登录modal）
    page.goto('https://wolt.com/en/fin', timeout=30000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    try: page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except: pass
    page.wait_for_timeout(2000)
    page.screenshot(path=f'{SHOT}/_signup_home.png')
    
    # 点 Sign up
    try:
        page.locator('[data-test-id="UserStatus.Signup"]').click(timeout=5000)
        print('clicked Sign up')
    except Exception as e:
        print(f'Signup click fail: {e}')
    
    page.wait_for_timeout(5000)
    page.screenshot(path=f'{SHOT}/_signup_modal.png')
    
    # 提取 modal 内所有输入框
    modal_inputs = page.evaluate("""() => {
        const out = [];
        const containers = document.querySelectorAll('[role="dialog"], .modal, [class*="Modal"], [class*="dialog"]');
        for (const c of containers) {
            for (const i of c.querySelectorAll('input, select')) {
                out.push({
                    tag: i.tagName,
                    type: i.type || '',
                    name: i.name || '',
                    placeholder: i.placeholder || '',
                    testid: i.getAttribute('data-test-id') || '',
                    aria: i.getAttribute('aria-label') || '',
                    required: i.required,
                    value: i.value || '',
                    autocomplete: i.autocomplete || ''
                });
            }
        }
        return out;
    }""")
    
    if not modal_inputs:
        # 可能不在 dialog 里，全局搜
        all_inputs = page.evaluate("""() => {
            const out = [];
            for (const i of document.querySelectorAll('input, select')) {
                out.push({
                    tag: i.tagName,
                    type: i.type || '',
                    name: i.name || '',
                    placeholder: i.placeholder || '',
                    testid: i.getAttribute('data-test-id') || '',
                    required: i.required,
                    autocomplete: i.autocomplete || ''
                });
            }
            return out;
        }""")
        print('ALL INPUTS:')
        for inp in all_inputs:
            print(f'  {inp["tag"]} type={inp["type"]} placeholder="{inp["placeholder"]}" testid="{inp["testid"]}" required={inp["required"]}')
    else:
        print('MODAL INPUTS:')
        for inp in modal_inputs:
            print(f'  {inp["tag"]} type={inp["type"]} placeholder="{inp["placeholder"]}" name="{inp["name"]}" required={inp["required"]} autocomplete="{inp["autocomplete"]}"')
    
    # 所有按钮
    btns = page.evaluate("""() => [...document.querySelectorAll('button, [role="button"]')].map(b => ({
        text: (b.textContent || '').trim().slice(0,60),
        type: b.type || '',
        testid: b.getAttribute('data-test-id') || ''
    })).filter(b => b.text)""")
    print('\nBUTTONS:')
    seen = set()
    for b in btns:
        k = b['text']
        if k not in seen:
            seen.add(k)
            print(f'  "{b["text"]}" testid={b["testid"]}')
    
    # 看 URL 和标题
    print(f'\nURL: {page.url}')
    print(f'TITLE: {page.title()}')
    
    # 看页面上可见文字（找注册说明）
    visible_text = page.evaluate("""() => {
        const texts = [];
        document.querySelectorAll('h1,h2,h3,h4,p,span,label').forEach(el => {
            if (el.offsetParent !== null) {
                const t = el.textContent.trim();
                if (t && t.length < 80) texts.push(t);
            }
        });
        return texts.slice(0, 20);
    }""")
    print('\nVISIBLE TEXT:')
    for t in visible_text[:15]:
        print(f'  "{t}"')
    
    br.close()
