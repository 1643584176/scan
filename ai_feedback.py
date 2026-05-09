#!/usr/bin/env python3
"""
AI反馈学习工具
用于人工验证扫描结果，让AI从反馈中学习和进化
"""

import json
import os
from ai_analyzer import get_ai_analyzer


def interactive_feedback():
    """交互式反馈界面"""
    analyzer = get_ai_analyzer()
    
    print("\n" + "="*60)
    print("🤖 AI漏洞分析 - 反馈学习系统")
    print("="*60 + "\n")
    
    # 显示最近的扫描记录
    stats = analyzer.get_statistics()
    print(f"📊 当前统计:")
    print(f"   - 总扫描次数: {stats['total_scans']}")
    print(f"   - 发现漏洞总数: {stats['total_vulns_found']}")
    print(f"   - 误报数量: {stats['false_positives']}")
    if stats['total_vulns_found'] > 0:
        accuracy = (1 - stats['false_positives'] / max(stats['total_vulns_found'], 1)) * 100
        print(f"   - 准确率: {accuracy:.1f}%")
    print()
    
    # 列出最近的扫描
    history = analyzer.knowledge_base['scan_history']
    if not history:
        print("暂无扫描记录，请先运行 automate_scan.py")
        return
    
    print("最近的扫描记录:")
    for i, record in enumerate(reversed(history[-10:]), 1):
        print(f"{i}. {record['domain']} - 风险:{record['risk_level']} "
              f"({len(record['analyzed_vulns'])}个漏洞)")
    
    print("\n请选择要反馈的域名（输入域名或序号）:")
    choice = input("> ").strip()
    
    # 查找对应的记录
    selected_record = None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(history):
            selected_record = history[-(idx + 1)]
    else:
        for record in history:
            if record['domain'] == choice:
                selected_record = record
                break
    
    if not selected_record:
        print("❌ 未找到对应的扫描记录")
        return
    
    domain = selected_record['domain']
    print(f"\n正在处理: {domain}")
    print(f"发现 {len(selected_record['analyzed_vulns'])} 个漏洞:\n")
    
    # 显示漏洞列表并收集反馈
    feedback = {}
    for i, vuln in enumerate(selected_record['analyzed_vulns'], 1):
        fp_marker = " ⚠️ 可能误报" if vuln.get('is_false_positive') else ""
        print(f"{i}. [{vuln['severity'].upper()}] {vuln['type']}{fp_marker}")
        print(f"   描述: {vuln['description'][:100]}...")
        print(f"   置信度: {vuln.get('confidence', 0):.0%}")
        print(f"   确认? [y/n/skip]: ", end="")
        
        answer = input().strip().lower()
        vuln_id = vuln.get('raw', str(i))
        
        if answer == 'y':
            feedback[vuln_id] = 'confirmed'
            print("   ✅ 已标记为确认")
        elif answer == 'n':
            feedback[vuln_id] = 'false_positive'
            print("   ❌ 已标记为误报")
        else:
            print("   ⏭️  跳过")
    
    # 提交反馈
    if feedback:
        print("\n正在更新AI知识库...")
        analyzer.learn_from_feedback(domain, feedback)
        print("✅ 学习完成！AI模型已根据反馈优化")
        
        # 显示更新后的统计
        stats = analyzer.get_statistics()
        if stats['total_vulns_found'] > 0:
            accuracy = (1 - stats['false_positives'] / stats['total_vulns_found']) * 100
            print(f"   当前准确率: {accuracy:.1f}%")
    else:
        print("没有收到反馈")


def export_knowledge():
    """导出知识库"""
    analyzer = get_ai_analyzer()
    
    output_file = input("导出文件名 [knowledge_export.json]: ").strip()
    if not output_file:
        output_file = 'knowledge_export.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analyzer.knowledge_base, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 知识库已导出到: {output_file}")


def show_statistics():
    """显示详细统计"""
    analyzer = get_ai_analyzer()
    stats = analyzer.get_statistics()
    
    print("\n" + "="*60)
    print("📊 AI知识库统计报告")
    print("="*60 + "\n")
    
    print(f"总扫描次数: {stats['total_scans']}")
    print(f"发现漏洞总数: {stats['total_vulns_found']}")
    print(f"误报数量: {stats['false_positives']}")
    if stats['total_vulns_found'] > 0:
        accuracy = (1 - stats['false_positives'] / stats['total_vulns_found']) * 100
        print(f"准确率: {accuracy:.1f}%")
    
    # 漏洞类型分布
    print("\n漏洞类型分布:")
    vuln_type_count = {}
    for record in analyzer.knowledge_base['scan_history']:
        for vuln in record.get('analyzed_vulns', []):
            vuln_type = vuln.get('type', 'unknown')
            vuln_type_count[vuln_type] = vuln_type_count.get(vuln_type, 0) + 1
    
    sorted_vulns = sorted(vuln_type_count.items(), key=lambda x: x[1], reverse=True)
    for vuln_type, count in sorted_vulns[:10]:
        percentage = count / sum(vuln_type_count.values()) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {vuln_type:20s} {count:4d} ({percentage:5.1f}%) {bar}")
    
    print("\n最近扫描记录:")
    history = analyzer.knowledge_base['scan_history'][-10:]
    for record in reversed(history):
        print(f"  {record['timestamp']} | {record['domain']:30s} | "
              f"{record['risk_level']:6s} | {len(record['analyzed_vulns'])}个漏洞")


def main():
    print("\n选择操作:")
    print("1. 提供反馈（训练AI）")
    print("2. 查看统计")
    print("3. 导出知识库")
    print("4. 生成AI分析报告")
    print("0. 退出")
    
    choice = input("\n请选择 [0-4]: ").strip()
    
    if choice == '1':
        interactive_feedback()
    elif choice == '2':
        show_statistics()
    elif choice == '3':
        export_knowledge()
    elif choice == '4':
        analyzer = get_ai_analyzer()
        output = input("报告文件名 [ai_analysis_report.md]: ").strip()
        if not output:
            output = 'ai_analysis_report.md'
        analyzer.export_report(output)
    elif choice == '0':
        print("再见！")
        return
    else:
        print("无效选择")
    
    # 循环
    main()


if __name__ == "__main__":
    main()
