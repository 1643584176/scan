#!/usr/bin/env python3
"""
自动化扫描脚本。
从 urls/ 目录读取URL文件，针对每个URL运行技术栈检测和漏洞扫描，
生成扫描报告。
"""

import sys
import os
import io
# 设置 stdout/stderr 为 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # 设置环境变量，让子进程也使用 UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'  # Python 3.7+
    # 设置 Windows 控制台编码为 UTF-8
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # CP_UTF8
    except:
        pass

import warnings
warnings.filterwarnings('ignore')  # 抑制所有警告（包括 subprocess 的 UnicodeDecodeError）

import json
import shutil
import subprocess
import time
from urllib.parse import urlparse
from datetime import datetime

def log(message):
    """输出带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)  # 强制刷新输出缓冲区

def get_domain(url):
    parsed = urlparse(url)
    return parsed.netloc

def parse_whatweb(json_file):
    with open(json_file, encoding='utf-8') as f:
        techs = json.load(f)
    # Wappalyzer 可能返回 dict 或 list，需要兼容处理
    if isinstance(techs, dict):
        return list(techs.keys())
    elif isinstance(techs, list):
        return techs
    else:
        return []

def parse_nuclei(txt_file):
    """解析Nuclei扫描结果"""
    with open(txt_file, encoding='utf-8') as f:
        content = f.read()
    return content

def update_nuclei():
    """智能更新Nuclei模板和引擎（静默执行）"""
    try:
        # 检查当前版本信息 - 不使用 text=True 避免编码问题
        check_result = subprocess.run(
            ['nuclei', '-update-templates', '-silent'], 
            capture_output=True,
            timeout=60
        )
        
        output = (check_result.stdout + check_result.stderr).decode('utf-8', errors='ignore')
        
        # 检查引擎是否需要更新
        engine_outdated = 'outdated' in output.lower()
        templates_latest = 'latest' in output.lower() or 'up-to-date' in output.lower()
        
        if templates_latest and not engine_outdated:
            return
        
        # 需要更新
        if engine_outdated:
            update_result = subprocess.run(
                ['nuclei', '-update'], 
                capture_output=True,
                timeout=300
            )
        else:
            update_result = subprocess.run(
                ['nuclei', '-update-templates'], 
                capture_output=True,
                timeout=300
            )
            
    except:
        pass

def update_katana():
    """更新Katana到最新版本（静默执行）"""
    try:
        # 使用 go_tools.py 更新
        subprocess.run(
            [sys.executable, os.path.join(os.getcwd(), 'tools', 'go_tools.py'), 'install', 'katana'],
            capture_output=True,
            timeout=300
        )
    except:
        pass

def update_httpx():
    """更新httpx到最新版本（静默执行）"""
    try:
        # 使用 go_tools.py 更新
        subprocess.run(
            [sys.executable, os.path.join(os.getcwd(), 'tools', 'go_tools.py'), 'install', 'httpx'],
            capture_output=True,
            timeout=300
        )
    except:
        pass

def update_sqlmap():
    """更新SQLMap到最新版本（静默执行）"""
    try:
        # 使用 pip 更新 sqlmap - 不使用 text=True 避免编码问题
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'sqlmap'],
            capture_output=True,
            timeout=120
        )
    except:
        pass

def main():
    # 加载 .env 配置文件
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # 只设置未定义的环境变量（命令行优先级更高）
                        if key not in os.environ:
                            os.environ[key] = value
            log("[OK] 已加载 .env 配置文件")
        except Exception as e:
            log(f"[WARN] 加载 .env 文件失败: {e}")
    
    # 启动时自动更新所有工具（静默执行）
    import concurrent.futures
    
    log("="*60)
    log("自动化安全扫描器 v2.0")
    log("="*60)
    
    log("\n[INFO] 检查工具更新...")
    log("[INFO] 这可能需要1-2分钟，请耐心等待...\n")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_nuclei = executor.submit(update_nuclei)
        future_katana = executor.submit(update_katana)
        future_httpx = executor.submit(update_httpx)
        future_sqlmap = executor.submit(update_sqlmap)
        
        # 等待所有更新任务完成
        future_nuclei.result()
        future_katana.result()
        future_httpx.result()
        future_sqlmap.result()
    
    log("[OK] 工具更新检查完成\n")

    urls_dir = 'urls'
    if not os.path.exists(urls_dir):
        log("urls/ 目录不存在。")
        return

    for file in os.listdir(urls_dir):
        if file.endswith('.txt'):
            with open(os.path.join(urls_dir, file), encoding='utf-8') as f:
                # 过滤掉注释行和空行
                urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

            for url in urls:
                log(f"开始扫描: {url}")
                domain = get_domain(url)
                bounty_dir = f"@{domain}_bounty"
                
                # 如果目录不存在，则创建
                if not os.path.exists(bounty_dir):
                    os.makedirs(bounty_dir, exist_ok=True)
                    log(f"创建目录 {bounty_dir}")

                # 技术栈检测（使用 httpx）
                log("\n" + "="*60)
                log("[步骤1/4] 开始: HTTP 探测")
                log("="*60)
                try:
                    # 使用 httpx 进行基本的 HTTP 探测
                    import shutil
                    httpx_exe = shutil.which('httpx-toolkit') or shutil.which('httpx') or 'httpx'
                    
                    # 如果找到的是 Python 的 httpx，尝试直接使用 Go bin 路径
                    if 'python' in httpx_exe.lower() or 'scripts' in httpx_exe.lower():
                        go_bin_paths = [
                            os.path.expanduser('~\\go\\bin\\httpx.exe'),
                            os.path.expanduser('~\\.local\\bin\\httpx'),
                            '/usr/local/bin/httpx',
                        ]
                        for path in go_bin_paths:
                            if os.path.exists(path):
                                httpx_exe = path
                                break
                    
                    result = subprocess.run([
                        httpx_exe,
                        '-u', url,
                        '-silent',
                        '-sc', '-title', '-tech-detect'
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        log("[✓] 步骤1完成: HTTP探测")
                        # 解析技术栈信息
                        tech_stack = []
                        tech_details = {}
                        for line in result.stdout.splitlines():
                            if line.strip():
                                parts = line.split()
                                if len(parts) > 2:
                                    # 尝试提取技术信息
                                    tech_stack.append('HTTP')
                    else:
                        log("[!] 步骤1警告: HTTP探测返回非零退出码")
                        tech_stack = []
                        tech_details = {}
                except subprocess.TimeoutExpired:
                    log("[✗] 步骤1失败: HTTP探测超时，已跳过")
                    tech_stack = []
                    tech_details = {}
                except Exception as e:
                    log(f"[✗] 步骤1失败: HTTP探测异常 - {e}")
                    tech_stack = []
                    tech_details = {}

                # URL 收集
                log("\n" + "="*60)
                log("[步骤2/4] 开始: URL 收集")
                log("="*60)
                log("   [INFO] 如果已有all_urls.txt，将直接使用（秒级完成）")
                log("   [INFO] Katana 爬虫正在运行，请稍候...")
                log("   [TIP] 这个过程可能需要3-10分钟，取决于目标网站大小\n")
                
                # 检查是否已有 all_urls.txt
                all_urls_check = os.path.join(bounty_dir, 'all_urls.txt')
                if os.path.exists(all_urls_check):
                    with open(all_urls_check, 'r', encoding='utf-8') as f:
                        existing_urls = [line.strip() for line in f if line.strip()]
                    if existing_urls:
                        log(f"   [OK] 发现已有的 all_urls.txt ({len(existing_urls)} 个 URL)，跳过爬取")
                        continue
                
                try:
                    # 直接运行 url_collector.py，让它自己处理输出
                    result = subprocess.run([
                        sys.executable,
                        os.path.join(os.getcwd(), 'tools', 'nikto', 'url_collector.py'),
                        url,
                        os.path.abspath(bounty_dir)
                    ], cwd=os.getcwd(), timeout=600)  # 10分钟超时
                    
                    if result.returncode == 0:
                        log("\n[✓] 步骤2完成: URL收集")
                    else:
                        log(f"\n[!] 步骤2警告: URL收集返回码 {result.returncode}")
                        log(f"   [INFO] 请检查 {bounty_dir}/all_urls.txt 是否生成")
                except subprocess.TimeoutExpired:
                    log("\n[✗] 步骤2失败: URL收集超时（10分钟），已跳过")
                    log(f"   [INFO] 尝试使用已有的 all_urls.txt")
                except Exception as e:
                    log(f"\n[✗] 步骤2失败: URL收集异常 - {e}")
                    import traceback
                    log(f"   [DEBUG] {traceback.format_exc()[:200]}")
                
                # 读取 all_urls.txt
                all_urls_file = os.path.join(bounty_dir, 'all_urls.txt')
                if not os.path.exists(all_urls_file):
                    log("未找到 all_urls.txt")
                    continue
                
                with open(all_urls_file, 'r', encoding='utf-8') as f:
                    all_urls = [line.strip() for line in f if line.strip()]
                
                # 如果文件存在但内容为空，删除它并重新爬取
                if not all_urls:
                    log("all_urls.txt 为空，删除后重新爬取...")
                    os.remove(all_urls_file)
                    # 重新调用 URL 收集器 - 显示输出
                    subprocess.run([
                        sys.executable,
                        os.path.join(os.getcwd(), 'tools', 'nikto', 'url_collector.py'),
                        url,
                        os.path.abspath(bounty_dir)
                    ], cwd=os.getcwd())
                    
                    # 再次读取
                    if not os.path.exists(all_urls_file):
                        log("重新爬取后仍未生成 all_urls.txt")
                        continue
                    with open(all_urls_file, 'r', encoding='utf-8') as f:
                        all_urls = [line.strip() for line in f if line.strip()]
                
                log(f"加载 {len(all_urls)} 个有效 URL")
                
                # URL 分类和分析
                log("\n" + "="*60)
                log("[步骤3/4] 开始: URL 分类分析")
                log("="*60)
                try:
                    result = subprocess.run([
                        sys.executable,
                        os.path.join(os.getcwd(), 'tools', 'nikto', 'url_analyzer.py'),
                        os.path.abspath(all_urls_file),
                        os.path.abspath(bounty_dir)
                    ], cwd=os.getcwd(), timeout=120)  # 2分钟超时
                    
                    if result.returncode == 0:
                        log("[✓] 步骤4完成: URL分类")
                except Exception as e:
                    log(f"[✗] 步骤4失败: URL分类异常 - {e}")
                
                # Nuclei 漏洞扫描
                log("\n" + "="*60)
                log("[步骤4/4] 开始: Nuclei 漏洞扫描")
                log("="*60)
                log("   [INFO] Nuclei扫描需要3-5分钟，请耐心等待...")
                log("   [TIP] 您将看到实时进度，如: [0:00:05] | Requests: 115/8118 (1%)")
                try:
                    # 不使用capture_output，直接显示实时输出
                    result = subprocess.run([
                        sys.executable,
                        os.path.join(os.getcwd(), 'tools', 'nikto', 'scan.py'),
                        url,
                        os.path.abspath(bounty_dir)
                    ], cwd=os.getcwd(), timeout=900)  # 15分钟超时
                    
                    if result.returncode == 0:
                        log("[✓] 步骤5完成: Nuclei扫描")
                    else:
                        log(f"[!] 步骤5警告: Nuclei扫描返回码 {result.returncode}")
                        
                        # 检查是否有输出文件
                        nuclei_file = os.path.join(bounty_dir, 'nuclei_scan.txt')
                        if os.path.exists(nuclei_file):
                            with open(nuclei_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if content.strip():
                                    log(f"   [INFO] 扫描结果已保存到: {nuclei_file}")
                                    lines = [line.strip() for line in content.splitlines() if line.strip()]
                                    log(f"   [INFO] 发现 {len(lines)} 个结果")
                except subprocess.TimeoutExpired:
                    log("[✗] 步骤5失败: Nuclei扫描超时（15分钟），已跳过")
                except Exception as e:
                    log(f"[✗] 步骤5失败: Nuclei扫描异常 - {e}")
                
                # 第四步：JavaScript 文件分析 - 显示输出
                log("\n" + "="*60)
                log("[步骤6/6] 开始: JavaScript 文件分析")
                log("="*60)
                try:
                    result = subprocess.run([
                        sys.executable,
                        os.path.join(os.getcwd(), 'tools', 'nikto', 'js_analyzer.py'),
                        os.path.abspath(all_urls_file),
                        os.path.abspath(bounty_dir)
                    ], cwd=os.getcwd(), timeout=300)  # 5分钟超时
                    
                    if result.returncode == 0:
                        log("[✓] 步骤6完成: JS分析")
                except Exception as e:
                    log(f"[✗] 步骤6失败: JS分析异常 - {e}")
                
                # 查找生成的 SQLMap 目标文件
                sqlmap_targets_file = os.path.join(bounty_dir, 'sqlmap_targets.txt')
                
                if os.path.exists(sqlmap_targets_file):
                    log(f"SQLMap 目标文件: {sqlmap_targets_file}")
                    
                    # 读取并显示统计
                    with open(sqlmap_targets_file, 'r', encoding='utf-8') as f:
                        sqlmap_urls = [line.strip() for line in f if line.strip()]
                    log(f"待测试 URL: {len(sqlmap_urls)} 个")
                else:
                    log("未生成 SQLMap 目标文件")
                    continue
                
                # SQLMap 注入测试 - 显示输出
                if os.path.exists(sqlmap_targets_file):
                    log("\n" + "="*60)
                    log("[额外步骤] 开始: SQLMap 注入测试（快速模式）")
                    log("="*60)
                    log("   [INFO] 快速模式：level=1, risk=1, 单URL最多3分钟")
                    log("   [INFO] 预计总时间: 8-15分钟（取决于目标响应速度）")
                    try:
                        result = subprocess.run([
                            sys.executable,
                            os.path.join(os.getcwd(), 'tools', 'nikto', 'sqlmap_scan.py'),
                            os.path.abspath(sqlmap_targets_file),
                            os.path.abspath(bounty_dir)
                        ], cwd=os.getcwd(), timeout=1200)  # 20分钟超时（快速模式）
                        
                        if result.returncode == 0:
                            log("[✓] 额外步骤完成: SQLMap测试")
                        else:
                            log(f"[!] 额外步骤警告: SQLMap测试返回码 {result.returncode}")
                    except subprocess.TimeoutExpired:
                        log("[✗] 额外步骤失败: SQLMap测试超时（20分钟），已跳过")
                    except Exception as e:
                        log(f"[✗] 额外步骤失败: SQLMap测试异常 - {e}")
                else:
                    log("\n[INFO] 跳过 SQLMap 测试（无带参数的目标 URL）")

                # 生成扫描报告
                findings_path = os.path.join(bounty_dir, 'findings.md')
                progress_path = os.path.join(bounty_dir, 'progress.md')
                readme_path = os.path.join(bounty_dir, 'README.md')

                # 读取 SQLMap 结果（使用固定文件名）
                sqlmap_results = []
                sqlmap_results_file = os.path.join(bounty_dir, 'sqlmap_results.json')
                if os.path.exists(sqlmap_results_file):
                    try:
                        with open(sqlmap_results_file, 'r', encoding='utf-8') as f:
                            sqlmap_data = json.load(f)
                            sqlmap_results = sqlmap_data.get('results', [])
                    except:
                        pass
                
                # 读取 Nuclei 扫描结果
                nuclei_results = []
                nuclei_file = os.path.join(bounty_dir, 'nuclei_scan.txt')
                if os.path.exists(nuclei_file):
                    try:
                        with open(nuclei_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 统计发现的漏洞数量（每行一个漏洞）
                            lines = [line.strip() for line in content.splitlines() if line.strip()]
                            nuclei_results = lines
                    except:
                        pass

                # 更新 findings.md
                with open(findings_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n## {url} 扫描结果\n")
                    f.write(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("### 技术栈\n")
                    for tech in tech_stack:
                        f.write(f"- {tech}\n")
                    f.write("\n")
                    
                    f.write("### URL 分类统计\n")
                    f.write(f"- **总 URL 数**: {len(all_urls)}\n")
                    f.write(f"- **API 端点**: {len([u for u in all_urls if '/api/' in u.lower() or u.lower().endswith('.json')])}\n")
                    f.write(f"- **带参数页面**: {len([u for u in all_urls if '?' in u])}\n")
                    f.write(f"- **登录/认证**: {len([u for u in all_urls if any(k in u.lower() for k in ['/login', '/auth', '/signin'])])}\n")
                    f.write(f"- **管理后台**: {len([u for u in all_urls if any(k in u.lower() for k in ['/admin', '/dashboard'])])}\n\n")
                    
                    # Nuclei 漏洞扫描结果
                    if nuclei_results:
                        f.write("### Nuclei 漏洞扫描\n\n")
                        f.write(f"- **发现漏洞**: {len(nuclei_results)} 个\n\n")
                        f.write("#### 漏洞详情:\n\n")
                        for i, vuln in enumerate(nuclei_results[:20], 1):  # 只显示前20个
                            f.write(f"{i}. `{vuln[:150]}`\n")
                        if len(nuclei_results) > 20:
                            f.write(f"\n... 还有 {len(nuclei_results) - 20} 个漏洞\n")
                        f.write("\n")
                    else:
                        f.write("### Nuclei 漏洞扫描\n\n")
                        f.write("- 未发现明显漏洞\n\n")
                    
                    if sqlmap_results:
                        f.write("### SQLMap 注入测试\n\n")
                        vulnerable_count = sum(1 for r in sqlmap_results if r.get('vulnerable'))
                        f.write(f"- **测试总数**: {len(sqlmap_results)}\n")
                        f.write(f"- **发现漏洞**: {vulnerable_count}\n\n")
                        
                        if vulnerable_count > 0:
                            f.write("#### 发现的注入点:\n\n")
                            for i, result in enumerate(sqlmap_results, 1):
                                if result.get('vulnerable'):
                                    f.write(f"{i}. `{result['url'][:100]}`\n")
                            f.write("\n")
                    else:
                        f.write("### SQLMap 测试\n\n")
                        f.write("- 无带参数的 URL，跳过 SQLMap 测试\n\n")
                    
                    f.write("---\n\n")

                # 更新 progress.md
                with open(progress_path, 'a', encoding='utf-8') as f:
                    f.write(f"- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: 扫描 {url} 完成\n")

                # 更新 README.md
                with open(readme_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n## 扫描总结 - {url}\n\n")
                    f.write(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"- **目标**: {url}\n")
                    f.write(f"- **技术栈**: {', '.join(tech_stack)}\n")
                    f.write(f"- **URL 数量**: {len(all_urls)}\n")
                    f.write(f"- **Nuclei 漏洞**: {len(nuclei_results)} 个\n")
                    f.write(f"- **SQLMap 测试**: {len(sqlmap_results)} 个 URL\n\n")

if __name__ == "__main__":
    main()
