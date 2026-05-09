#!/usr/bin/env python3
"""
自动化扫描脚本（AI增强版）。
从 urls/ 目录读取URL文件，针对每个URL运行技术栈检测和漏洞扫描，
使用AI智能分析结果，生成新的赏金目录并总结报告。
"""

import os
import json
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse
from datetime import datetime
from ai_analyzer import get_ai_analyzer

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
    nuclei_exe = os.path.join(os.getcwd(), 'tools', 'nuclei', 'nuclei.exe')
    
    if not os.path.exists(nuclei_exe):
        return
    
    try:
        # 检查当前版本信息
        check_result = subprocess.run(
            [nuclei_exe, '-update-templates', '-silent'], 
            capture_output=True, 
            text=True,
            timeout=60
        )
        
        output = check_result.stdout + check_result.stderr
        
        # 检查引擎是否需要更新
        engine_outdated = 'outdated' in output.lower()
        templates_latest = 'latest' in output.lower() or 'up-to-date' in output.lower()
        
        if templates_latest and not engine_outdated:
            return
        
        # 需要更新
        if engine_outdated:
            update_result = subprocess.run(
                [nuclei_exe, '-update'], 
                capture_output=True, 
                text=True,
                timeout=300
            )
        else:
            update_result = subprocess.run(
                [nuclei_exe, '-update-templates'], 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
    except:
        pass

def update_sqlmap():
    """更新SQLMap到最新版本（静默执行）"""
    try:
        # 使用 pip 更新 sqlmap
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'sqlmap'],
            capture_output=True,
            text=True,
            timeout=120
        )
    except:
        pass

def main():
    # 启动时自动更新工具（静默执行）
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_nuclei = executor.submit(update_nuclei)
        future_sqlmap = executor.submit(update_sqlmap)
        
        # 等待两个更新任务完成
        future_nuclei.result()
        future_sqlmap.result()

    urls_dir = 'urls'
    if not os.path.exists(urls_dir):
        print("urls/ 目录不存在。")
        return

    for file in os.listdir(urls_dir):
        if file.endswith('.txt'):
            with open(os.path.join(urls_dir, file), encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]

            for url in urls:
                domain = get_domain(url)
                bounty_dir = f"@{domain}_bounty"
                
                # 如果目录不存在，则创建
                if not os.path.exists(bounty_dir):
                    shutil.copytree('example_bounty', bounty_dir)
                    print(f"创建目录 {bounty_dir}")

                # 技术栈检测（Wappalyzer + HTTP头/HTML分析）
                subprocess.run([sys.executable, os.path.join(os.getcwd(), 'tools', 'whatweb', 'scan.py'), url], cwd=bounty_dir, capture_output=True)
                
                # 增强检测：HTTP头和HTML分析
                enhanced_result = subprocess.run(
                    [sys.executable, os.path.join(os.getcwd(), 'tools', 'whatweb', 'scan_enhanced.py'), url],
                    cwd=bounty_dir,
                    capture_output=True,
                    text=True
                )
                
                # 如果增强检测有错误，静默跳过（不显示）
                # if enhanced_result.returncode != 0 and enhanced_result.stderr:
                #     print(f"⚠️  增强检测警告: {enhanced_result.stderr[:200]}")

                # 解析技术栈信息（合并 Wappalyzer 和增强检测的结果）
                tech_stack = []
                tech_details = {}
                
                # 1. 解析 Wappalyzer 结果
                for file in os.listdir(bounty_dir):
                    if file.startswith('wappalyzer_') and file.endswith('.json'):
                        tech_file = os.path.join(bounty_dir, file)
                        with open(tech_file, 'r', encoding='utf-8') as f:
                            tech_data = json.load(f)
                        
                        if isinstance(tech_data, dict):
                            for tech_name, tech_info in tech_data.items():
                                version = ''
                                if isinstance(tech_info, dict) and 'version' in tech_info:
                                    version = f" v{tech_info['version']}"
                                elif isinstance(tech_info, list) and len(tech_info) > 0:
                                    version = f" v{tech_info[0]}"
                                tech_details[tech_name] = version
                                tech_stack.append(tech_name)
                        elif isinstance(tech_data, list):
                            for tech in tech_data:
                                if tech not in tech_stack:
                                    tech_stack.append(tech)
                                    tech_details[tech] = ''
                        break
                
                # 2. 解析增强检测结果（HTTP头 + HTML）
                for file in os.listdir(bounty_dir):
                    if file.startswith('enhanced_') and file.endswith('.json'):
                        tech_file = os.path.join(bounty_dir, file)
                        try:
                            with open(tech_file, 'r', encoding='utf-8') as f:
                                enhanced_data = json.load(f)
                            
                            # 合并增强检测到的技术（去重）
                            for tech_name, version in enhanced_data.items():
                                if tech_name not in tech_details:
                                    tech_details[tech_name] = f" v{version}" if version else ''
                                    tech_stack.append(tech_name)
                        except:
                            pass
                        break
                
                # 显示技术栈（带版本号）
                if tech_details:
                    tech_list = [f"{name}{ver}" for name, ver in tech_details.items()]
                    print(f"✅ 技术栈: {', '.join(tech_list)}")
                else:
                    print(f"✅ 技术栈: {', '.join(tech_stack) if tech_stack else '未检测到'}")

                # 第一步：URL 收集（增量扫描）
                print("\n🔍 启动 URL 收集...")
                subprocess.run([
                    sys.executable,
                    os.path.join(os.getcwd(), 'tools', 'nikto', 'url_collector.py'),
                    url,
                    bounty_dir
                ], cwd=bounty_dir)
                
                # 读取 all_urls.txt
                all_urls_file = os.path.join(bounty_dir, 'all_urls.txt')
                if not os.path.exists(all_urls_file):
                    print("❌ 未找到 all_urls.txt")
                    continue
                
                with open(all_urls_file, 'r', encoding='utf-8') as f:
                    all_urls = [line.strip() for line in f if line.strip()]
                
                print(f"✅ 加载 {len(all_urls)} 个有效 URL\n")
                
                # 第二步：从 all_urls.txt 中提取带参数的 URL
                print("📊 提取带参数的 URL...")
                from urllib.parse import urlparse
                
                param_urls = []
                for target_url in all_urls:
                    parsed = urlparse(target_url)
                    if parsed.query:  # 有查询参数
                        param_urls.append(target_url)
                
                # 去重
                param_urls = list(set(param_urls))
                
                if param_urls:
                    print(f"✅ 发现 {len(param_urls)} 个带参数的 URL")
                    # 保存参数 URL 到文件，供 SQLMap 使用
                    params_file = os.path.join(bounty_dir, f'nuclei_params_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
                    with open(params_file, 'w', encoding='utf-8') as f:
                        for purl in param_urls:
                            f.write(purl + '\n')
                    print(f"💾 参数已保存: {params_file}")
                else:
                    print("⚠️  未发现带参数的 URL")
                
                # 第三步：Nuclei 扫描（使用 all_urls.txt）
                print("\n🚀 启动 Nuclei 扫描...")
                # 将 all_urls.txt 传递给 Nuclei
                nuclei_input_file = os.path.join(bounty_dir, 'all_urls.txt')
                subprocess.run([
                    sys.executable, 
                    os.path.join(os.getcwd(), 'tools', 'nikto', 'scan_enhanced.py'), 
                    nuclei_input_file,  # 传递文件而不是单个 URL
                    'fast'
                ], cwd=bounty_dir)
                
                # 第四步：SQLMap 注入测试
                if param_urls:
                    print("\n💉 启动 SQLMap 注入测试...")
                    subprocess.run([
                        sys.executable,
                        os.path.join(os.getcwd(), 'tools', 'nikto', 'sqlmap_scan.py'),
                        params_file,
                        bounty_dir
                    ], cwd=bounty_dir)

                # 解析输出并更新文件
                findings_path = os.path.join(bounty_dir, 'findings.md')
                progress_path = os.path.join(bounty_dir, 'progress.md')
                readme_path = os.path.join(bounty_dir, 'README.md')

                scan_output = ''

                for file in os.listdir(bounty_dir):
                    if file.startswith('nuclei_') and file.endswith('.txt'):
                        scan_output = parse_nuclei(os.path.join(bounty_dir, file))
                        break

                # AI智能分析

                # 🤖 AI智能分析
                ai_analyzer = get_ai_analyzer()
                ai_result = ai_analyzer.analyze_scan_results(
                    tech_stack=tech_stack,
                    scan_output=scan_output,
                    domain=domain,
                    url=url
                )

                # 更新 findings.md（AI增强版）
                with open(findings_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n## {url} 扫描结果\n")
                    f.write(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("### 🎯 技术栈\n")
                    for tech in tech_stack:
                        f.write(f"- {tech}\n")
                    f.write("\n")
                    
                    f.write("### 🛡️ AI智能分析\n")
                    f.write(f"- **风险等级**: {ai_result['risk_level']} ({ai_result['risk_score']}/10)\n")
                    f.write(f"- **原始告警数**: {ai_result['raw_vuln_count']}\n")
                    f.write(f"- **AI分析后**: {len(ai_result['analyzed_vulns'])}个潜在漏洞\n\n")
                    
                    if ai_result['analyzed_vulns']:
                        f.write("### 📋 漏洞详情\n\n")
                        for i, vuln in enumerate(ai_result['analyzed_vulns'], 1):
                            fp_marker = " ⚠️ 可能误报" if vuln.get('is_false_positive') else ""
                            f.write(f"#### {i}. {vuln['type']}{fp_marker}\n")
                            f.write(f"- **严重程度**: {vuln['severity']}\n")
                            f.write(f"- **置信度**: {vuln.get('confidence', 0):.0%}\n")
                            f.write(f"- **优先级**: {vuln.get('priority', 'N/A')}\n")
                            f.write(f"- **描述**: {vuln['description']}\n\n")
                    
                    if ai_result.get('similar_cases'):
                        f.write("### 🔍 相似案例\n\n")
                        for case in ai_result['similar_cases'][:3]:
                            f.write(f"- **{case['domain']}**: 相似度{case['similarity']:.0%}, "
                                  f"发现{case['vulns_found']}个漏洞, 风险:{case['risk_level']}\n")
                        f.write("\n")
                    
                    if ai_result.get('recommendations'):
                        f.write("### 💡 修复建议\n\n")
                        for rec in ai_result['recommendations']:
                            f.write(f"- {rec}\n")
                        f.write("\n")
                    
                    f.write(f"### 📝 AI总结\n\n{ai_result['summary']}\n\n")
                    f.write("---\n\n")

                # 更新 progress.md
                with open(progress_path, 'a', encoding='utf-8') as f:
                    f.write(f"- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: 扫描 {url} 完成\n")

                # 更新 README.md（AI增强版）
                with open(readme_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n## 🤖 AI扫描总结 - {url}\n\n")
                    f.write(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"- **目标**: {url}\n")
                    f.write(f"- **技术栈**: {', '.join(tech_stack)}\n")
                    f.write(f"- **风险等级**: {ai_result['risk_level']} ({ai_result['risk_score']}/10)\n")
                    f.write(f"- **漏洞数量**: {len(ai_result['analyzed_vulns'])}\n\n")
                    
                    if ai_result['risk_score'] >= 6.0:
                        f.write("🚨 **高风险目标，需要立即人工验证和修复！**\n\n")
                    elif ai_result['risk_score'] >= 4.0:
                        f.write("⚠️  **中等风险，建议优先处理**\n\n")
                    elif ai_result['risk_score'] > 0:
                        f.write("✅ 低风险，持续监控即可\n\n")
                    else:
                        f.write("✅ 当前安全，定期扫描即可\n\n")
                    
                    if ai_result.get('recommendations'):
                        f.write("**关键建议**:\n")
                        for rec in ai_result['recommendations'][:3]:
                            f.write(f"- {rec}\n")
                        f.write("\n")

if __name__ == "__main__":
    main()
