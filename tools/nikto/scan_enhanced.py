#!/usr/bin/env python3
"""
Nuclei 漏洞扫描包装脚本（增强版）。
用法: python scan_enhanced.py <目标URL> [scan_mode]
扫描模式:
  - fast: 快速扫描（只使用高危模板）
  - normal: 普通扫描（默认，平衡速度和覆盖率）
  - full: 完整扫描（所有模板，最彻底但最慢）
"""

import subprocess
import sys
import os
from datetime import datetime
import threading
import time

def run_nuclei(target, mode='normal', tech_stack=None):
    output_file = f"nuclei_scan_{target.replace('http://', '').replace('https://', '').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    nuclei_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'nuclei', 'nuclei.exe')
    
    # 根据不同模式配置扫描参数和模板筛选（仅Web网页端）
    configs = {
        'fast': {
            'concurrency': 10,
            'timeout': 8,
            'rate_limit': 150,
            'retries': 0,
            'severity': 'critical,high',
            'tags': '',
            'exclude_tags': 'fuzz,headless,network,dns,ssl,file,osint,mobile,app,android,ios,takeover,exposure,misconfig,info',
            'description': '快速扫描'
        },
        'normal': {
            'concurrency': 8,
            'timeout': 8,
            'rate_limit': 100,
            'retries': 0,
            'severity': 'critical,high,medium',
            'tags': '',
            'exclude_tags': 'fuzz,headless,info,network,dns,ssl,file,osint,mobile,app,android,ios,takeover,exposure,misconfig',
            'description': '普通扫描'
        },
        'full': {
            'concurrency': 5,
            'timeout': 8,
            'rate_limit': 50,
            'retries': 0,
            'severity': 'critical,high,medium,low',
            'tags': '',
            'exclude_tags': 'fuzz,headless,network,dns,ssl,file,osint,mobile,app,android,ios',
            'description': '完整扫描'
        }
    }
    
    config = configs.get(mode, configs['normal'])
    
    # 构建基础命令（移除 -silent 以显示进度）
    command = [
        nuclei_exe, "-u", target, "-o", output_file,
        "-c", str(config['concurrency']),
        "-timeout", str(config['timeout']),
        "-rate-limit", str(config['rate_limit']),
        "-retries", str(config['retries']),
        "-severity", config['severity'],
        "-exclude-tags", config['exclude_tags'],
        "-stats"  # 移除 -silent，保留 -stats
    ]
    
    # 如果没有技术栈信息，使用默认的 Web 漏洞标签（排除 sqli，由 SQLMap 负责）
    if not tech_stack or len(tech_stack) == 0:
        default_tags = 'xss,rce,lfi,rfi,ssrf,csrf,cors,crlf'
        command.extend(['-tags', default_tags])
    
    # 如果提供了技术栈信息，构建针对性的标签组合
    if tech_stack and len(tech_stack) > 0:
        # 基础 Web 漏洞标签（排除 sqli，由 SQLMap 负责）
        base_tags = ['xss', 'rce', 'lfi', 'rfi', 'ssrf', 'csrf']
        
        # 根据技术栈添加特定标签
        tech_specific_tags = []
        for tech in tech_stack:
            tech_lower = tech.lower().replace(' ', '-')
            # 常见技术栈映射
            if 'wordpress' in tech_lower:
                tech_specific_tags.extend(['wordpress'])
            elif 'joomla' in tech_lower:
                tech_specific_tags.extend(['joomla'])
            elif 'drupal' in tech_lower:
                tech_specific_tags.extend(['drupal'])
            elif 'apache' in tech_lower:
                tech_specific_tags.extend(['apache'])
            elif 'nginx' in tech_lower:
                tech_specific_tags.extend(['nginx'])
            elif 'php' in tech_lower:
                tech_specific_tags.extend(['php'])
            elif 'java' in tech_lower or 'spring' in tech_lower:
                tech_specific_tags.extend(['java'])
            elif 'python' in tech_lower or 'django' in tech_lower or 'flask' in tech_lower:
                tech_specific_tags.extend(['python'])
            elif 'node' in tech_lower or 'express' in tech_lower:
                tech_specific_tags.extend(['nodejs'])
            elif 'laravel' in tech_lower:
                tech_specific_tags.extend(['laravel'])
        
        # 合并标签（去重）
        all_tags = list(set(base_tags + tech_specific_tags))
        tags_str = ','.join(all_tags)
        command.extend(['-tags', tags_str])
        
        print(f"🎯 针对性扫描: {', '.join(tech_stack)}")
        if tech_specific_tags:
            print(f"   特定模板: {', '.join(set(tech_specific_tags))}")
    
    try:
        # 使用 Popen 实现实时输出
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        start_time = datetime.now()
        matched_count = 0
        total_requests = 0
        last_error_count = 0
        scan_complete = threading.Event()
        templates_loaded = 0
        
        # 后台线程：定期显示扫描状态（只在 Nuclei 没有输出时显示）
        last_nuclei_output = datetime.now()
        
        def show_progress():
            elapsed = 0
            while not scan_complete.is_set():
                time.sleep(5)  # 每5秒更新一次
                elapsed += 5
                elapsed_min = elapsed // 60
                elapsed_sec = elapsed % 60
                
                # 如果最近 10 秒内没有 Nuclei 输出，才显示后台进度
                if (datetime.now() - last_nuclei_output).total_seconds() > 10:
                    if total_requests > 0:
                        print(f"\r  ⏳ 扫描中... [{elapsed_min}分{elapsed_sec}秒] | 请求:{total_requests:,} | 发现:{matched_count}   ", end='', flush=True)
                    else:
                        print(f"\r  ⏳ 扫描中... [{elapsed_min}分{elapsed_sec}秒]   ", end='', flush=True)
        
        # 启动后台线程
        progress_thread = threading.Thread(target=show_progress, daemon=True)
        progress_thread.start()
        
        # 实时显示扫描进度
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            
            # 调试：打印前几行输出（仅用于调试）
            # print(f"DEBUG: {line}")
            
            # 解析进度信息格式: [0:00:05] | Templates: 11577 | Hosts: 1 | RPS: 152 | Matched: 0 | Errors: 759 | Requests: 764/18968 (4%)
            if 'Requests:' in line and '%' in line:
                try:
                    import re
                    # 提取关键数据
                    matched_match = re.search(r'Matched:\s*(\d+)', line)
                    requests_match = re.search(r'Requests:\s*(\d+)/(\d+)\s*\((\d+)%\)', line)
                    rps_match = re.search(r'RPS:\s*(\d+)', line)
                    errors_match = re.search(r'Errors:\s*(\d+)', line)
                    
                    if requests_match:
                        current_req = int(requests_match.group(1))
                        total_req = int(requests_match.group(2))
                        percent = int(requests_match.group(3))
                        
                        # 更新全局变量供后台线程使用
                        total_requests = total_req
                        
                        if matched_match:
                            matched_count = int(matched_match.group(1))
                        
                        errors = errors_match.group(1) if errors_match else '0'
                        error_count = int(errors)
                        
                        # 计算错误率（不显示警告，因为有防护的网站错误率高是正常的）
                        # error_rate = (error_count / current_req * 100) if current_req > 0 else 0
                        # 
                        # # 如果错误率超过50%，发出警告（提高阈值）
                        # if error_rate > 50 and error_count > last_error_count:
                        #     print(f"\n  ⚠️  错误率过高: {error_rate:.1f}%")
                        #     last_error_count = error_count
                        
                        # 计算剩余时间（只在进度>5%时才显示，避免早期估算不准）
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if percent >= 5 and current_req > 0:
                            estimated_total = elapsed / (percent / 100)
                            remaining = estimated_total - elapsed
                            remaining_min = int(remaining // 60)
                            remaining_sec = int(remaining % 60)
                            if remaining_min > 0:
                                time_str = f"{remaining_min}分{remaining_sec}秒"
                            else:
                                time_str = f"{remaining_sec}秒"
                        else:
                            time_str = "计算中..."
                        
                        # 显示进度条（简化版）
                        bar_length = 20
                        filled = int(bar_length * percent / 100)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        
                        # 更新最后输出时间
                        last_nuclei_output = datetime.now()
                        
                        # 只显示关键信息：进度、请求、发现、错误
                        if error_count > 0:
                            print(f"\r  [{bar}] {percent}% | 请求:{current_req}/{total_requests} | 发现:{matched_count} | 错误:{error_count} | 剩余:{time_str}", end='', flush=True)
                        else:
                            print(f"\r  [{bar}] {percent}% | 请求:{current_req}/{total_requests} | 发现:{matched_count} | 剩余:{time_str}", end='', flush=True)
                except Exception as e:
                    pass
        
        # 换行
        print("\n" + "-" * 60)
        
        # 停止后台线程
        scan_complete.set()
        progress_thread.join(timeout=2)
        
        process.wait()
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        elapsed_min = int(elapsed_time // 60)
        elapsed_sec = int(elapsed_time % 60)
        
        if process.returncode == 0:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            elapsed_min = int(elapsed_time // 60)
            elapsed_sec = int(elapsed_time % 60)
            
            print(f"\n✅ 扫描完成！")
            print(f"⏱️  耗时: {elapsed_min}分{elapsed_sec}秒")
            print(f"📋 模板: {templates_loaded:,} 个")
            print(f"🎯 发现漏洞: {matched_count} 个")
            print(f"💾 结果: {output_file}")
            
            # 如果有漏洞，显示简要信息
            if matched_count > 0:
                print(f"\n📄 查看: type {output_file}")
        else:
            print(f"❌ 扫描失败，返回码: {process.returncode}")
            
    except FileNotFoundError:
        print("未找到Nuclei。请确保nuclei.exe在tools/nuclei/目录下。")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scan_enhanced.py <目标URL或URL文件> [scan_mode]")
        print("扫描模式: fast, normal (默认), full")
        print("\n示例:")
        print("  python scan_enhanced.py http://example.com fast")
        print("  python scan_enhanced.py urls.txt normal")
        sys.exit(1)
    
    target = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'normal'
    
    if mode not in ['fast', 'normal', 'full']:
        print(f"错误: 无效的扫描模式 '{mode}'")
        print("可用的模式: fast, normal, full")
        sys.exit(1)
    
    # 判断是 URL 还是文件
    if os.path.exists(target):
        # 从文件读取 URL 列表
        with open(target, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and line.startswith('http')]
        print(f"📂 从文件加载 {len(urls)} 个 URL: {target}")
        
        # 对每个 URL 执行扫描
        for url in urls:
            run_nuclei(url, mode)
    else:
        # 单个 URL
        run_nuclei(target, mode)
