#!/usr/bin/env python3
"""
Nuclei 漏洞扫描包装脚本。
用法: python scan.py <目标URL>
"""

import subprocess
import sys
import os
from datetime import datetime

def run_nuclei(target, mode='normal', tech_stack=None):
    output_file = f"nuclei_scan_{target.replace('http://', '').replace('https://', '').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    nuclei_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'nuclei', 'nuclei.exe')
    
    # 根据不同模式配置扫描参数和模板筛选（仅Web网页端）
    configs = {
        'fast': {
            'concurrency': 5,
            'timeout': 10,
            'rate_limit': 100,
            'retries': 1,
            'severity': 'critical,high',  # 只扫描严重和高危漏洞
            'tags': '',  # 不限制标签
            'exclude_tags': 'fuzz,headless,network,dns,ssl,file,osint,mobile,app,android,ios',  # 排除非Web和移动端
            'description': '快速扫描（仅高危Web漏洞）'
        },
        'normal': {
            'concurrency': 3,
            'timeout': 15,
            'rate_limit': 50,
            'retries': 2,
            'severity': 'critical,high,medium',  # 扫描中高危及严重漏洞
            'tags': '',  # 不限制标签
            'exclude_tags': 'fuzz,headless,info,network,dns,ssl,file,osint,mobile,app,android,ios',  # 排除非Web和移动端
            'description': '普通扫描（推荐，仅Web网页端）'
        },
        'full': {
            'concurrency': 2,
            'timeout': 20,
            'rate_limit': 30,
            'retries': 3,
            'severity': 'critical,high,medium,low',  # 扫描所有漏洞
            'tags': '',  # 不限制标签
            'exclude_tags': 'fuzz,headless,network,dns,ssl,file,osint,mobile,app,android,ios',  # 排除非Web和移动端
            'description': '完整扫描（最彻底，仅Web网页端）'
        }
    }
    
    config = configs.get(mode, configs['normal'])
    
    # 构建基础命令
    command = [
        nuclei_exe, "-u", target, "-o", output_file,
        "-c", str(config['concurrency']),
        "-timeout", str(config['timeout']),
        "-rate-limit", str(config['rate_limit']),
        "-retries", str(config['retries']),
        "-severity", config['severity'],
        "-exclude-tags", config['exclude_tags'],
        "-stats", "-silent"
    ]
    
    # 如果提供了技术栈信息，只使用相关模板
    if tech_stack and len(tech_stack) > 0:
        # 将技术栈转换为小写并用逗号分隔
        tech_tags = ','.join([tech.lower().replace(' ', '-') for tech in tech_stack])
        command.extend(['-tags', tech_tags])
        print(f"🎯 针对性扫描: 仅使用与 {', '.join(tech_stack)} 相关的Web模板")
    
    try:
        print(f"🚀 开始 Nuclei 漏洞扫描...")
        print(f"🎯 目标: {target}")
        print(f"📊 模式: {config['description']}")
        print(f"⚙️  配置: 并发={config['concurrency']}, 超时={config['timeout']}s, 速率限制={config['rate_limit']}req/s")
        print(f"🔍 严重级别: {config['severity']}")
        print(f"🚫 排除标签: {config['exclude_tags']}")
        print(f"💾 输出文件: {output_file}")
        print("=" * 60)
        
        # 使用 Popen 实现实时输出
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        start_time = datetime.now()
        matched_count = 0
        total_requests = 0
        last_error_count = 0
        
        # 实时显示扫描进度
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            
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
                        
                        if total_requests == 0:
                            total_requests = total_req
                            print(f"📋 总请求数: {total_requests}")
                            print("-" * 60)
                        
                        if matched_match:
                            matched_count = int(matched_match.group(1))
                        
                        rps = rps_match.group(1) if rps_match else '0'
                        errors = errors_match.group(1) if errors_match else '0'
                        error_count = int(errors)
                        
                        # 计算错误率
                        error_rate = (error_count / current_req * 100) if current_req > 0 else 0
                        
                        # 如果错误率超过30%，发出警告
                        if error_rate > 30 and error_count > last_error_count:
                            print(f"\n  ⚠️  错误率过高: {error_rate:.1f}% ({error_count}/{current_req})")
                            print(f"  💡 建议: 目标可能有WAF防护，考虑降低速率限制")
                            last_error_count = error_count
                        
                        # 计算剩余时间
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if percent > 0 and current_req > 0:
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
                        
                        # 显示进度条
                        bar_length = 30
                        filled = int(bar_length * percent / 100)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        
                        # 根据错误率改变颜色提示
                        if error_rate > 30:
                            status_icon = "⚠️"
                        elif error_rate > 10:
                            status_icon = "🔶"
                        else:
                            status_icon = "📊"
                        
                        print(f"\r  {status_icon} [{bar}] {percent}% | "
                              f"请求:{current_req}/{total_requests} | "
                              f"RPS:{rps} | "
                              f"发现:{matched_count} | "
                              f"错误:{errors}({error_rate:.1f}%) | "
                              f"剩余:{time_str}", end='', flush=True)
                except Exception as e:
                    pass
        
        # 换行
        print("\n" + "=" * 60)
        
        process.wait()
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        elapsed_min = int(elapsed_time // 60)
        elapsed_sec = int(elapsed_time % 60)
        
        if process.returncode == 0:
            print(f"✅ 扫描完成！")
            print(f"⏱️  耗时: {elapsed_min}分{elapsed_sec}秒")
            print(f"🎯 发现漏洞: {matched_count} 个")
            print(f"💾 结果已保存到: {output_file}")
            
            # 如果有漏洞，显示简要信息
            if matched_count > 0:
                print(f"\n📄 查看详细信息:")
                print(f"   cat {output_file}")
        else:
            print(f"❌ 扫描失败，返回码: {process.returncode}")
            
    except FileNotFoundError:
        print("未找到Nuclei。请确保nuclei.exe在tools/nuclei/目录下。")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python scan.py <目标URL>")
        sys.exit(1)
    target = sys.argv[1]
    run_nuclei(target)
