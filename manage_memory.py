#!/usr/bin/env python3
"""
AI记忆管理工具 - 查看、备份、恢复AI的记忆
"""

import os
import json
import shutil
from datetime import datetime


def show_memory_status():
    """显示AI记忆状态"""
    print("\n" + "="*60)
    print("🧠 AI记忆状态检查")
    print("="*60 + "\n")
    
    # 检查知识库文件
    kb_file = 'knowledge_base.json'
    if os.path.exists(kb_file):
        with open(kb_file, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
        
        stats = kb_data.get('statistics', {})
        history = kb_data.get('scan_history', [])
        
        print(f"✅ 知识库文件: {kb_file}")
        print(f"   创建时间: {kb_data.get('created_at', '未知')}")
        print(f"   文件大小: {os.path.getsize(kb_file) / 1024:.2f} KB")
        print(f"\n📊 统计数据:")
        print(f"   - 总扫描次数: {stats.get('total_scans', 0)}")
        print(f"   - 发现漏洞总数: {stats.get('total_vulns_found', 0)}")
        print(f"   - 误报数量: {stats.get('false_positives', 0)}")
        
        if stats.get('total_scans', 0) > 0:
            accuracy = (1 - stats.get('false_positives', 0) / 
                       max(stats.get('total_vulns_found', 1), 1)) * 100
            print(f"   - 当前准确率: {accuracy:.1f}%")
        
        print(f"\n📜 最近扫描记录:")
        for record in history[-5:]:
            print(f"   [{record['timestamp']}] {record['domain']} - "
                  f"风险:{record['risk_level']} ({len(record['analyzed_vulns'])}个漏洞)")
    else:
        print("❌ 知识库文件不存在（尚未进行任何扫描）")
    
    # 检查向量数据库
    vector_db_path = 'ai_memory_db'
    if os.path.exists(vector_db_path):
        total_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(vector_db_path)
                        for filename in filenames)
        print(f"\n✅ 向量数据库: {vector_db_path}/")
        print(f"   总大小: {total_size / 1024 / 1024:.2f} MB")
    else:
        print(f"\n⚠️  向量数据库不存在（将在首次扫描时创建）")
    
    print()


def backup_memory():
    """备份AI记忆"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'ai_memory_backup_{timestamp}'
    
    print(f"\n💾 正在备份AI记忆到: {backup_dir}/\n")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    # 备份知识库
    if os.path.exists('knowledge_base.json'):
        shutil.copy2('knowledge_base.json', backup_dir)
        print("✅ 已备份: knowledge_base.json")
    
    # 备份向量数据库
    if os.path.exists('ai_memory_db'):
        shutil.copytree('ai_memory_db', os.path.join(backup_dir, 'ai_memory_db'))
        print("✅ 已备份: ai_memory_db/")
    
    # 创建备份说明
    with open(os.path.join(backup_dir, 'backup_info.txt'), 'w', encoding='utf-8') as f:
        f.write(f"AI记忆备份\n")
        f.write(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n还原方法:\n")
        f.write(f"1. 将 {backup_dir}/knowledge_base.json 复制到项目根目录\n")
        f.write(f"2. 将 {backup_dir}/ai_memory_db/ 复制到项目根目录\n")
        f.write(f"3. 覆盖现有文件即可\n")
    
    print(f"✅ 备份完成！")
    print(f"\n📦 备份位置: {backup_dir}/")
    print()


def restore_memory(backup_dir):
    """恢复AI记忆"""
    if not os.path.exists(backup_dir):
        print(f"❌ 备份目录不存在: {backup_dir}")
        return
    
    print(f"\n🔄 正在从 {backup_dir}/ 恢复AI记忆...\n")
    
    # 恢复知识库
    kb_file = os.path.join(backup_dir, 'knowledge_base.json')
    if os.path.exists(kb_file):
        shutil.copy2(kb_file, 'knowledge_base.json')
        print("✅ 已恢复: knowledge_base.json")
    else:
        print("⚠️  未找到: knowledge_base.json")
    
    # 恢复向量数据库
    vector_db = os.path.join(backup_dir, 'ai_memory_db')
    if os.path.exists(vector_db):
        if os.path.exists('ai_memory_db'):
            shutil.rmtree('ai_memory_db')
        shutil.copytree(vector_db, 'ai_memory_db')
        print("✅ 已恢复: ai_memory_db/")
    else:
        print("⚠️  未找到: ai_memory_db/")
    
    print(f"\n✅ 记忆恢复完成！")
    print(f"运行 python test_ai.py 验证系统状态\n")


def clear_memory():
    """清空AI记忆（重置）"""
    print("\n⚠️  警告: 这将清空所有AI记忆数据！")
    confirm = input("确认清空？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("已取消")
        return
    
    print("\n🗑️  正在清空AI记忆...\n")
    
    # 删除知识库
    if os.path.exists('knowledge_base.json'):
        os.remove('knowledge_base.json')
        print("✅ 已删除: knowledge_base.json")
    
    # 删除向量数据库
    if os.path.exists('ai_memory_db'):
        shutil.rmtree('ai_memory_db')
        print("✅ 已删除: ai_memory_db/")
    
    print("\n✅ AI记忆已清空，系统将重新开始学习\n")


def export_memory_summary():
    """导出记忆摘要报告"""
    if not os.path.exists('knowledge_base.json'):
        print("❌ 没有可导出的记忆数据")
        return
    
    with open('knowledge_base.json', 'r', encoding='utf-8') as f:
        kb_data = json.load(f)
    
    output_file = f'ai_memory_report_{datetime.now().strftime("%Y%m%d")}.md'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 🧠 AI记忆分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 统计信息
        stats = kb_data.get('statistics', {})
        f.write("## 📊 总体统计\n\n")
        f.write(f"- 总扫描次数: {stats.get('total_scans', 0)}\n")
        f.write(f"- 发现漏洞总数: {stats.get('total_vulns_found', 0)}\n")
        f.write(f"- 误报数量: {stats.get('false_positives', 0)}\n")
        
        if stats.get('total_vulns_found', 0) > 0:
            accuracy = (1 - stats.get('false_positives', 0) / 
                       stats.get('total_vulns_found', 1)) * 100
            f.write(f"- 准确率: {accuracy:.1f}%\n")
        
        f.write("\n## 🔥 常见漏洞类型\n\n")
        vuln_patterns = kb_data.get('vuln_patterns', {})
        sorted_patterns = sorted(vuln_patterns.items(), 
                                key=lambda x: x[1].get('count', 0), 
                                reverse=True)
        
        for vuln_type, data in sorted_patterns[:10]:
            f.write(f"- **{vuln_type}**: {data.get('count', 0)}次 "
                   f"(首次: {data.get('first_seen', 'N/A')})\n")
        
        f.write("\n## 📜 完整扫描历史\n\n")
        f.write("| 时间 | 域名 | 技术栈 | 漏洞数 | 风险等级 |\n")
        f.write("|------|------|--------|-------|---------|\n")
        
        for record in kb_data.get('scan_history', []):
            tech_str = ', '.join(record.get('tech_stack', [])[:3])
            f.write(f"| {record['timestamp']} | {record['domain']} | "
                   f"{tech_str} | {len(record.get('analyzed_vulns', []))} | "
                   f"{record['risk_level']} |\n")
    
    print(f"✅ 记忆报告已导出: {output_file}")


def main():
    print("\n选择操作:")
    print("1. 查看记忆状态")
    print("2. 备份记忆")
    print("3. 恢复记忆")
    print("4. 清空记忆（重置）")
    print("5. 导出记忆报告")
    print("0. 退出")
    
    choice = input("\n请选择 [0-5]: ").strip()
    
    if choice == '1':
        show_memory_status()
    elif choice == '2':
        backup_memory()
    elif choice == '3':
        backup_dir = input("输入备份目录名: ").strip()
        restore_memory(backup_dir)
    elif choice == '4':
        clear_memory()
    elif choice == '5':
        export_memory_summary()
    elif choice == '0':
        print("再见！")
        return
    else:
        print("无效选择")


if __name__ == "__main__":
    main()

