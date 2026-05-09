#!/usr/bin/env python3
"""
SQLMap 自动化注入测试工具。
用法: python sqlmap_scan.py <目标URL或参数文件> [输出目录]
"""

import subprocess
import json
import os
import sys
from datetime import datetime

def load_sensitive_params(params_file):
    """加载敏感参数文件"""
    if not os.path.exists(params_file):
        print(f"⚠️  参数文件不存在: {params_file}")
        return {}
    
    with open(params_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_sqlmap_on_url(url, output_dir, level=2, risk=2):
    """对单个 URL 运行 SQLMap"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'sqlmap_{timestamp}.txt')
    
    # 查找 sqlmap.py
    sqlmap_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'sqlmap', 'sqlmap.py'),
        os.path.join(os.getcwd(), 'tools', 'sqlmap', 'sqlmap.py'),
        'sqlmap.py'  # 如果在 PATH 中
    ]
    
    sqlmap_exe = None
    for path in sqlmap_paths:
        if os.path.exists(path):
            sqlmap_exe = path
            break
    
    if not sqlmap_exe:
        print(f"⚠️  SQLMap 未找到，跳过测试")
        print(f"💡 安装方法: pip install sqlmap 或下载 sqlmap.py")
        return {
            'url': url,
            'output_file': None,
            'vulnerable': False,
            'error': 'SQLMap not found'
        }
    
    cmd = [
        sys.executable, sqlmap_exe,
        '-u', url,
        '--batch',           # 自动选择默认选项
        '--level', str(level),  # 测试等级 (1-5)
        '--risk', str(risk),    # 风险等级 (1-3)
        '--threads', '3',       # 线程数
        '--timeout', '10',      # 超时时间
        '--retries', '0',       # 不重试
        '--random-agent',       # 随机 User-Agent
        '--batch',              # 非交互模式
        '-o'                    # 启用所有优化
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 保存输出
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n=== STDERR ===\n")
                f.write(result.stderr)
        
        # 检查是否发现注入点
        is_vulnerable = 'is vulnerable' in result.stdout.lower() or 'injectable' in result.stdout.lower()
        
        return {
            'url': url,
            'output_file': output_file,
            'vulnerable': is_vulnerable,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'url': url,
            'output_file': output_file,
            'vulnerable': False,
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'url': url,
            'output_file': output_file,
            'vulnerable': False,
            'error': str(e)
        }

def load_urls_from_file(urls_file):
    """从文件加载 URL 列表（每行一个 URL）"""
    if not os.path.exists(urls_file):
        print(f"⚠️  URL 文件不存在: {urls_file}")
        return []
    
    urls = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and (url.startswith('http://') or url.startswith('https://')):
                urls.append(url)
    
    return urls

def scan_urls(urls, output_dir, limit=10):
    """扫描 URL 列表"""
    results = []
    
    print(f"\n🎯 开始 SQLMap 注入测试...")
    print(f"   测试级别: 2 (中等)")
    print(f"   风险等级: 2 (中等)")
    print(f"   待测试 URL: {len(urls)} 个")
    print(f"   最大测试数: {limit}\n")
    
    # 限制测试数量
    test_urls = urls[:limit]
    
    for i, url in enumerate(test_urls, 1):
        print(f"  [{i}/{len(test_urls)}] 测试: {url[:80]}...")
        
        result = run_sqlmap_on_url(url, output_dir)
        results.append(result)
        
        if result['vulnerable']:
            print(f"    ⚠️  发现 SQL 注入漏洞!")
        else:
            print(f"    ✅ 未发现漏洞")
    
    print(f"\n✅ SQLMap 扫描完成! 共测试 {len(results)} 个 URL")
    
    # 统计结果
    vulnerable_count = sum(1 for r in results if r.get('vulnerable'))
    print(f"   发现漏洞: {vulnerable_count} 个")
    print(f"   安全: {len(results) - vulnerable_count} 个")
    
    return results

def save_results(results, output_dir):
    """保存扫描结果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = os.path.join(output_dir, f'sqlmap_results_{timestamp}.json')
    
    summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_tested': len(results),
        'vulnerable_count': sum(1 for r in results if r.get('vulnerable')),
        'results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 结果已保存: {results_file}")
    return results_file

def run_sqlmap_scan(target, output_dir='.'):
    """主函数"""
    # 判断输入是 URL 列表文件还是参数 JSON 文件
    if os.path.exists(target):
        # 检查文件类型
        if target.endswith('.txt'):
            # URL 列表文件（每行一个 URL）
            print(f"📂 加载 URL 列表: {target}")
            urls = load_urls_from_file(target)
        elif target.endswith('.json'):
            # JSON 格式的参数文件（旧格式，兼容）
            print(f"📂 使用参数文件: {target}")
            sensitive_data = load_sensitive_params(target)
            if not sensitive_data:
                print("❌ 没有敏感参数可测试")
                return 0
            # 转换为 URL 列表
            urls = []
            for category, url_list in sensitive_data.items():
                urls.extend(url_list)
            urls = list(set(urls))  # 去重
        else:
            print(f"❌ 不支持的文件格式: {target}")
            return 0
    else:
        print(f"❌ 文件不存在: {target}")
        return 0
    
    if not urls:
        print("❌ 没有 URL 可测试")
        return 0
    
    # 执行扫描
    results = scan_urls(urls, output_dir, limit=10)
    
    # 保存结果
    if results:
        save_results(results, output_dir)
    
    return len(results)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python sqlmap_scan.py <URL列表文件或参数文件> [输出目录]")
        print("\n示例:")
        print("  python sqlmap_scan.py nuclei_params_20260509.txt ./bounty_dir")
        print("  python sqlmap_scan.py crawler_sensitive_20260509.json ./bounty_dir")
        sys.exit(1)
    
    target = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    run_sqlmap_scan(target, output_dir)
