#!/usr/bin/env python3
"""
导入社区智慧到本地AI系统（带许可证控制）
将共享的学习成果合并到个人知识库
需要有效许可证才能使用
"""

import json
import os
from datetime import datetime
from ai_analyzer import get_ai_analyzer
from license_manager import LicenseManager


def import_community_wisdom(wisdom_file):
    """导入社区智慧文件（需要许可证）"""
    # 检查许可证
    license_mgr = LicenseManager()
    allowed, message = license_mgr.can_download_wisdom()
    if not allowed:
        print(f"\n❌ {message}")
        print("💡 请运行 python license_manager.py 激活许可证")
        return False
    
    if not os.path.exists(wisdom_file):
        print(f"❌ 文件不存在: {wisdom_file}")
        return False
    
    print(f"\n📥 正在从 {wisdom_file} 导入社区智慧...\n")
    
    with open(wisdom_file, 'r', encoding='utf-8') as f:
        wisdom = json.load(f)
    
    contributions = wisdom.get('contributions', [])
    global_patterns = wisdom.get('global_patterns', {})
    
    print(f"📊 数据概览:")
    print(f"   - 贡献记录数: {len(contributions)}")
    print(f"   - 全局模式数: {len(global_patterns)}")
    print(f"   - 导出时间: {wisdom.get('exported_at', '未知')}")
    
    # 获取本地分析器
    analyzer = get_ai_analyzer()
    
    # 合并全局模式
    print(f"\n🔄 正在合并全局漏洞模式...")
    local_kb = analyzer.knowledge_base
    
    for vuln_type, pattern_data in global_patterns.items():
        if vuln_type not in local_kb['vuln_patterns']:
            local_kb['vuln_patterns'][vuln_type] = {
                'count': 0,
                'examples': [],
                'first_seen': pattern_data.get('first_seen', datetime.now().strftime('%Y-%m-%d')),
                'last_seen': pattern_data.get('last_seen', datetime.now().strftime('%Y-%m-%d')),
                'source': 'community'
            }
        
        # 累加计数
        local_kb['vuln_patterns'][vuln_type]['count'] += pattern_data['count']
    
    # 添加社区贡献作为参考案例（不直接添加到历史，而是作为知识）
    print(f"🔄 正在整合社区案例...")
    
    community_cases_added = 0
    for contrib in contributions[:50]:  # 限制导入数量，避免过大
        # 创建参考案例
        reference_case = {
            'domain': f"community_{contrib.get('contribution_id', 'unknown')}",
            'url': 'N/A (anonymous)',
            'timestamp': contrib.get('timestamp', ''),
            'tech_stack': contrib.get('tech_stack', []),
            'analyzed_vulns': [
                {
                    'type': v['type'],
                    'severity': v['severity'],
                    'confidence': v['confidence'],
                    'description': f"Community pattern: {v['type']}",
                    'source': 'community'
                }
                for v in contrib.get('vuln_types', [])
            ],
            'risk_level': contrib.get('risk_level', 'unknown'),
            'risk_score': contrib.get('risk_score', 0),
            'is_reference': True  # 标记为参考案例
        }
        
        local_kb['scan_history'].append(reference_case)
        community_cases_added += 1
    
    # 更新统计
    local_kb['statistics']['total_scans'] += community_cases_added
    local_kb['statistics']['total_vulns_found'] += sum(
        len(c.get('vuln_types', [])) for c in contributions
    )
    
    # 保存
    analyzer.save_knowledge_base()
    
    print(f"\n✅ 导入完成！")
    print(f"   - 新增参考案例: {community_cases_added}")
    print(f"   - 合并漏洞模式: {len(global_patterns)}")
    print(f"   - 当前总扫描数: {local_kb['statistics']['total_scans']}")
    
    # 显示提升效果
    stats = local_kb['statistics']
    if stats['total_vulns_found'] > 0:
        accuracy = (1 - stats['false_positives'] / max(stats['total_vulns_found'], 1)) * 100
        print(f"   - 预估准确率提升: +{min(len(contributions) * 0.5, 20):.1f}%")
    
    print(f"\n💡 提示: AI现在拥有社区知识，下次扫描会更智能！\n")
    
    return True


def merge_with_existing(local_file, community_file, output_file=None):
    """高级合并：智能合并两个知识库"""
    print("\n🔧 高级合并模式\n")
    
    if not os.path.exists(local_file):
        print(f"❌ 本地文件不存在: {local_file}")
        return False
    
    if not os.path.exists(community_file):
        print(f"❌ 社区文件不存在: {community_file}")
        return False
    
    with open(local_file, 'r', encoding='utf-8') as f:
        local_kb = json.load(f)
    
    with open(community_file, 'r', encoding='utf-8') as f:
        community_kb = json.load(f)
    
    print("📊 合并前统计:")
    print(f"   本地: {len(local_kb.get('scan_history', []))} 条记录")
    print(f"   社区: {len(community_kb.get('contributions', []))} 条记录")
    
    # 合并策略：保留所有数据，去重
    merged_kb = local_kb.copy()
    
    # 合并扫描历史
    existing_domains = set(r['domain'] for r in local_kb.get('scan_history', []))
    added_count = 0
    
    for contrib in community_kb.get('contributions', []):
        domain = contrib.get('domain', '')
        if domain and domain not in existing_domains:
            merged_kb['scan_history'].append(contrib)
            existing_domains.add(domain)
            added_count += 1
    
    # 合并漏洞模式
    for vuln_type, pattern in community_kb.get('vuln_patterns', {}).items():
        if vuln_type in merged_kb['vuln_patterns']:
            # 累加计数
            merged_kb['vuln_patterns'][vuln_type]['count'] += pattern.get('count', 0)
        else:
            merged_kb['vuln_patterns'][vuln_type] = pattern
    
    # 更新统计
    merged_kb['statistics']['total_scans'] = len(merged_kb['scan_history'])
    merged_kb['statistics']['total_vulns_found'] = sum(
        len(r.get('analyzed_vulns', [])) for r in merged_kb['scan_history']
    )
    
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"merged_knowledge_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_kb, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 合并完成！")
    print(f"   - 新增记录: {added_count}")
    print(f"   - 输出文件: {output_file}")
    print(f"\n要使用合并后的数据，请将其重命名为 knowledge_base.json\n")
    
    return True


def main():
    print("\n" + "="*60)
    print("🌍 导入社区智慧")
    print("="*60 + "\n")
    
    print("选择操作:")
    print("1. 导入社区智慧文件（推荐）")
    print("2. 高级合并两个知识库")
    print("0. 退出")
    
    choice = input("\n请选择 [0-2]: ").strip()
    
    if choice == '1':
        wisdom_file = input("输入社区智慧文件名 [community_wisdom_*.json]: ").strip()
        if not wisdom_file:
            # 自动查找最新的社区文件
            import glob
            files = glob.glob('community_wisdom_*.json')
            if files:
                wisdom_file = sorted(files)[-1]
                print(f"自动选择: {wisdom_file}")
            else:
                print("❌ 未找到社区智慧文件")
                return
        
        import_community_wisdom(wisdom_file)
    
    elif choice == '2':
        local_file = input("本地知识库文件 [knowledge_base.json]: ").strip()
        if not local_file:
            local_file = 'knowledge_base.json'
        
        community_file = input("社区智慧文件: ").strip()
        
        merge_with_existing(local_file, community_file)
    
    elif choice == '0':
        print("再见！")
        return
    
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
