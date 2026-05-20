#!/usr/bin/env python3
"""
SQLMap 自动化注入测试工具。
用法: python sqlmap_scan.py <目标URL或参数文件> [输出目录]
"""

import subprocess
import json
import os
import sys
import warnings
from datetime import datetime

# 设置 Windows 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except:
        pass

warnings.filterwarnings('ignore')  # 抑制所有警告

def log(message):
    """输出带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def load_sensitive_params(params_file):
    """加载敏感参数文件"""
    if not os.path.exists(params_file):
        log(f"参数文件不存在: {params_file}")
        return {}
    
    with open(params_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_sqlmap_on_url(url, output_dir, level=1, risk=1):
    """对单个 URL 运行 SQLMap（快速模式）"""
    # 使用固定文件名，不带时间戳
    output_file = os.path.join(output_dir, 'sqlmap_output.txt')
    
    # 查找 sqlmap.py
    sqlmap_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'sqlmap', 'sqlmap.py'),
        os.path.join(os.getcwd(), 'tools', 'sqlmap', 'sqlmap.py'),
        'sqlmap.py'  # 如果在 PATH 中
    ]
    
    # 尝试从 Python 包位置查找（pip 安装）
    try:
        import sqlmap
        import os as _os
        pip_sqlmap_path = _os.path.join(_os.path.dirname(sqlmap.__file__), 'sqlmap.py')
        if _os.path.exists(pip_sqlmap_path):
            sqlmap_paths.insert(0, pip_sqlmap_path)  # 优先使用 pip 安装的版本
    except ImportError:
        pass
    
    sqlmap_exe = None
    for path in sqlmap_paths:
        if os.path.exists(path):
            sqlmap_exe = path
            break
    
    if not sqlmap_exe:
        log("SQLMap 未找到，跳过测试")
        log("安装方法: pip install sqlmap 或下载 sqlmap.py")
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
        '--level', str(level),  # 测试等级 (1-5)，快速模式使用1
        '--risk', str(risk),    # 风险等级 (1-3)，快速模式使用1
        '--threads', '5',       # 线程数，增加到5
        '--timeout', '8',       # 超时时间，减少到8秒
        '--retries', '0',       # 不重试
        '--random-agent',       # 随机 User-Agent
        '--batch',              # 非交互模式
        '-o',                   # 启用所有优化
        '--smart'               # 智能模式，只进行最有效的测试
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            # 不使用 text=True，避免编码问题
            timeout=180  # 3分钟超时（快速模式）
        )
        
        # 解码输出
        stdout_text = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ''
        stderr_text = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
        
        # 保存输出
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(stdout_text)
            if stderr_text:
                f.write("\n=== STDERR ===\n")
                f.write(stderr_text)
        
        # 检查是否发现注入点（更精确的检测）
        stdout_lower = stdout_text.lower()
        # 只有明确说 "is vulnerable" 或 "injectable" 且不是 "not injectable" 才算漏洞
        is_vulnerable = False
        
        if 'is vulnerable' in stdout_lower:
            is_vulnerable = True
        elif 'injectable' in stdout_lower:
            # 排除 "not appear to be injectable" 和 "does not appear to be injectable"
            if 'not appear to be injectable' not in stdout_lower and \
               'does not appear to be injectable' not in stdout_lower and \
               'might not be injectable' not in stdout_lower:
                is_vulnerable = True
        
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
        log(f"URL 文件不存在: {urls_file}")
        return []
    
    urls = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and (url.startswith('http://') or url.startswith('https://')):
                urls.append(url)
    
    return urls

def scan_urls(urls, output_dir, limit=10):
    """扫描 URL 列表（快速模式）"""
    results = []
    
    log("\n开始 SQLMap 注入测试...（快速模式）")
    log("   测试级别: 1 (快速)")
    log("   风险等级: 1 (低)")
    log("   线程数: 5")
    log("   单URL超时: 3分钟")
    log(f"   待测试 URL: {len(urls)} 个")
    log(f"   最大测试数: {limit}")
    log("   [INFO] 快速模式牺牲部分准确性换取速度\n")
    
    # 限制测试数量
    test_urls = urls[:limit]
    
    for i, url in enumerate(test_urls, 1):
        log(f"  [{i}/{len(test_urls)}] 测试: {url[:80]}...")
        
        result = run_sqlmap_on_url(url, output_dir)
        results.append(result)
        
        if result['vulnerable']:
            log("    发现 SQL 注入漏洞!")
        else:
            log("    未发现漏洞")
    
    log(f"\nSQLMap 扫描完成! 共测试 {len(results)} 个 URL")
    
    # 统计结果
    vulnerable_count = sum(1 for r in results if r.get('vulnerable'))
    log(f"   发现漏洞: {vulnerable_count} 个")
    log(f"   安全: {len(results) - vulnerable_count} 个")
    
    return results

def save_results(results, output_dir):
    """保存扫描结果（使用固定文件名）"""
    # 使用固定文件名，不带时间戳
    results_file = os.path.join(output_dir, 'sqlmap_results.json')
    
    summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_tested': len(results),
        'vulnerable_count': sum(1 for r in results if r.get('vulnerable')),
        'results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    log(f"\n结果已保存: {results_file}")
    return results_file

def run_sqlmap_scan(target, output_dir='.'):
    """主函数"""
    # 判断输入是 URL 列表文件还是参数 JSON 文件
    if os.path.exists(target):
        # 检查文件类型
        if target.endswith('.txt'):
            # URL 列表文件（每行一个 URL）
            log(f"加载 URL 列表: {target}")
            urls = load_urls_from_file(target)
        elif target.endswith('.json'):
            # JSON 格式的参数文件（旧格式，兼容）
            log(f"使用参数文件: {target}")
            sensitive_data = load_sensitive_params(target)
            if not sensitive_data:
                log("没有敏感参数可测试")
                return 0
            # 转换为 URL 列表
            urls = []
            for category, url_list in sensitive_data.items():
                urls.extend(url_list)
            urls = list(set(urls))  # 去重
        else:
            log(f"不支持的文件格式: {target}")
            return 0
    else:
        log(f"文件不存在: {target}")
        return 0
    
    if not urls:
        log("没有 URL 可测试")
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
