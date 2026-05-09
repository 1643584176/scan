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
from urllib.parse import urlparse
from datetime import datetime
from ai_analyzer import get_ai_analyzer

def get_domain(url):
    parsed = urlparse(url)
    return parsed.netloc

def parse_whatweb(json_file):
    with open(json_file, encoding='utf-8') as f:
        techs = json.load(f)
    return list(techs.keys())

def parse_nuclei(txt_file):
    """解析Nuclei扫描结果"""
    with open(txt_file, encoding='utf-8') as f:
        content = f.read()
    return content

def update_nuclei():
    nuclei_exe = os.path.join(os.getcwd(), 'tools', 'nuclei', 'nuclei.exe')
    if os.path.exists(nuclei_exe):
        print("正在更新Nuclei模板...")
        try:
            result = subprocess.run([nuclei_exe, '-update-templates'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Nuclei模板更新完成。")
            else:
                print("更新失败:", result.stderr)
        except Exception as e:
            print(f"更新错误: {e}")
    else:
        print("Nuclei未找到，跳过更新。")

def main():
    print("启动项目，检查Nuclei更新...")
    update_nuclei()
    print("更新检查完成。\n")

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
                if os.path.exists(bounty_dir):
                    print(f"目录 {bounty_dir} 已存在，跳过。")
                    continue

                # 复制 example_bounty
                shutil.copytree('example_bounty', bounty_dir)
                print(f"创建目录 {bounty_dir}")

                # 运行 whatweb
                subprocess.run([sys.executable, 'tools/whatweb/scan.py', url], cwd=bounty_dir)

                # 运行 Nuclei 漏洞扫描
                subprocess.run([sys.executable, 'tools/nikto/scan.py', url], cwd=bounty_dir)

                # 解析输出并更新文件
                findings_path = os.path.join(bounty_dir, 'findings.md')
                progress_path = os.path.join(bounty_dir, 'progress.md')
                readme_path = os.path.join(bounty_dir, 'README.md')

                tech_stack = []
                scan_output = ''

                for file in os.listdir(bounty_dir):
                    if file.startswith('wappalyzer_') and file.endswith('.json'):
                        tech_stack = parse_whatweb(os.path.join(bounty_dir, file))
                    if file.startswith('nuclei_') and file.endswith('.txt'):
                        scan_output = parse_nuclei(os.path.join(bounty_dir, file))

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
