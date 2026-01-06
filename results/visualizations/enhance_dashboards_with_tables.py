#!/usr/bin/env python3
"""
为Dashboard添加更多表格来直观展现结论
"""

import json
import re
from pathlib import Path

def add_tables_to_core_users_dashboard(html_content, data_file):
    """为核心用户对比Dashboard添加表格"""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取数据文件失败: {e}")
        return html_content
    
    tables_html = ''
    
    # 1. 核心用户 vs 其他用户 - 兴趣对比表格
    if 'comparisons' in data and 'core_interests' in data['comparisons']:
        interests = data['comparisons']['core_interests']
        tables_html += '''
        <div class="section">
            <h2>核心用户 vs 其他用户 - 兴趣对比</h2>
            <table>
                <thead>
                    <tr>
                        <th>兴趣</th>
                        <th>核心用户占比</th>
                        <th>其他用户占比</th>
                        <th>差异</th>
                        <th>差异倍数</th>
                    </tr>
                </thead>
                <tbody>'''
        
        for item in interests[:15]:
            feature = item.get('feature', '')
            core_pct = item.get('core_percentage', 0)
            other_pct = item.get('other_percentage', 0)
            diff = item.get('difference', 0)
            ratio = core_pct / other_pct if other_pct > 0 else 0
            
            tables_html += f'''
                    <tr>
                        <td><strong>{feature}</strong></td>
                        <td>{core_pct:.1f}%</td>
                        <td>{other_pct:.1f}%</td>
                        <td style="color: {'#1a1a1a' if diff > 0 else '#999'};">{diff:+.1f}%</td>
                        <td>{ratio:.2f}x</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 2. 购买阶段对比表格
    if 'comparisons' in data and 'purchase_stages' in data['comparisons']:
        stages = data['comparisons']['purchase_stages']
        tables_html += '''
        <div class="section">
            <h2>核心用户 vs 其他用户 - 购买阶段对比</h2>
            <table>
                <thead>
                    <tr>
                        <th>购买阶段</th>
                        <th>核心用户占比</th>
                        <th>其他用户占比</th>
                        <th>差异</th>
                        <th>说明</th>
                    </tr>
                </thead>
                <tbody>'''
        
        for item in stages:
            feature = item.get('feature', '')
            core_pct = item.get('core_percentage', 0)
            other_pct = item.get('other_percentage', 0)
            diff = item.get('difference', 0)
            is_higher = item.get('is_core_higher', False)
            implication = "核心用户更倾向于此阶段" if is_higher else "其他用户更倾向于此阶段"
            
            tables_html += f'''
                    <tr>
                        <td><strong>{feature}</strong></td>
                        <td>{core_pct:.1f}%</td>
                        <td>{other_pct:.1f}%</td>
                        <td style="color: {'#1a1a1a' if diff > 0 else '#999'};">{diff:+.1f}%</td>
                        <td>{implication}</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 3. 关键属性对比表格
    if 'comparisons' in data and 'key_attributes' in data['comparisons']:
        attributes = data['comparisons']['key_attributes']
        tables_html += '''
        <div class="section">
            <h2>核心用户 vs 其他用户 - 关键属性对比</h2>
            <table>
                <thead>
                    <tr>
                        <th>属性</th>
                        <th>核心用户占比</th>
                        <th>其他用户占比</th>
                        <th>差异</th>
                        <th>差异倍数</th>
                    </tr>
                </thead>
                <tbody>'''
        
        for item in attributes[:15]:
            feature = item.get('feature', '')
            core_pct = item.get('core_percentage', 0)
            other_pct = item.get('other_percentage', 0)
            diff = item.get('difference', 0)
            ratio = core_pct / other_pct if other_pct > 0 else 0
            
            tables_html += f'''
                    <tr>
                        <td><strong>{feature}</strong></td>
                        <td>{core_pct:.1f}%</td>
                        <td>{other_pct:.1f}%</td>
                        <td style="color: {'#1a1a1a' if diff > 0 else '#999'};">{diff:+.1f}%</td>
                        <td>{ratio:.2f}x</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 4. 价格敏感度对比表格
    if 'comparisons' in data and 'price_ranges' in data['comparisons']:
        price_ranges = data['comparisons']['price_ranges']
        tables_html += '''
        <div class="section">
            <h2>核心用户 vs 其他用户 - 价格敏感度对比</h2>
            <table>
                <thead>
                    <tr>
                        <th>价格区间</th>
                        <th>核心用户占比</th>
                        <th>其他用户占比</th>
                        <th>差异</th>
                    </tr>
                </thead>
                <tbody>'''
        
        for item in price_ranges:
            feature = item.get('feature', '')
            core_pct = item.get('core_percentage', 0)
            other_pct = item.get('other_percentage', 0)
            diff = item.get('difference', 0)
            
            tables_html += f'''
                    <tr>
                        <td><strong>{feature}</strong></td>
                        <td>{core_pct:.1f}%</td>
                        <td>{other_pct:.1f}%</td>
                        <td style="color: {'#1a1a1a' if diff > 0 else '#999'};">{diff:+.1f}%</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 插入表格到合适位置（在第一个section之前）
    if tables_html:
        # 查找第一个section的位置
        pattern = r'(<div class="section">)'
        if re.search(pattern, html_content):
            html_content = re.sub(
                pattern,
                tables_html + r'\1',
                html_content,
                count=1
            )
        else:
            # 如果没有section，在content div后插入
            html_content = re.sub(
                r'(<div id="content">)',
                r'\1' + tables_html,
                html_content
            )
    
    return html_content

def add_tables_to_cluster_specific_dashboard(html_content, data_file):
    """为聚类特定分析Dashboard添加表格"""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取数据文件失败: {e}")
        return html_content
    
    tables_html = ''
    
    # 1. 聚类特征对比总览表格
    if 'cluster_analyses' in data:
        clusters = data['cluster_analyses']
        tables_html += '''
        <div class="section">
            <h2>聚类特征对比总览</h2>
            <table>
                <thead>
                    <tr>
                        <th>聚类ID</th>
                        <th>用户数</th>
                        <th>时间范围</th>
                        <th>差异化分数</th>
                        <th>独特兴趣数</th>
                        <th>独特属性数</th>
                        <th>主要特征</th>
                    </tr>
                </thead>
                <tbody>'''
        
        for cluster in clusters:
            cluster_id = cluster.get('cluster_id', '')
            size = cluster.get('size', 0)
            time_range = cluster.get('time_range', '')
            uniqueness = cluster.get('uniqueness', {})
            diff_score = uniqueness.get('differentiation_score', 0)
            unique_interests = uniqueness.get('unique_interests', [])
            unique_attributes = uniqueness.get('unique_attributes', [])
            
            # 获取主要特征
            main_features = []
            if unique_interests:
                main_features.append(unique_interests[0].get('interest', ''))
            if unique_attributes:
                main_features.append(unique_attributes[0].get('attribute', ''))
            main_feature = ', '.join(main_features[:2]) or 'N/A'
            
            tables_html += f'''
                    <tr>
                        <td><strong>{cluster_id}</strong></td>
                        <td>{size}</td>
                        <td>{time_range}</td>
                        <td>{diff_score:.2f}</td>
                        <td>{len(unique_interests)}</td>
                        <td>{len(unique_attributes)}</td>
                        <td>{main_feature}</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
        
        # 2. 独特特征排名表格（兴趣）
        all_unique_interests = {}
        for cluster in clusters:
            for interest in cluster.get('uniqueness', {}).get('unique_interests', []):
                interest_name = interest.get('interest', '')
                if interest_name:
                    if interest_name not in all_unique_interests:
                        all_unique_interests[interest_name] = {
                            'count': 0,
                            'max_ratio': 0,
                            'clusters': []
                        }
                    all_unique_interests[interest_name]['count'] += 1
                    ratio = interest.get('uniqueness_ratio', 0)
                    if ratio > all_unique_interests[interest_name]['max_ratio']:
                        all_unique_interests[interest_name]['max_ratio'] = ratio
                    all_unique_interests[interest_name]['clusters'].append(cluster.get('cluster_id', ''))
        
        if all_unique_interests:
            tables_html += '''
        <div class="section">
            <h2>独特兴趣排名（按独特性倍数）</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>兴趣</th>
                        <th>出现聚类数</th>
                        <th>最高独特性倍数</th>
                        <th>相关聚类</th>
                    </tr>
                </thead>
                <tbody>'''
            
            sorted_interests = sorted(
                all_unique_interests.items(),
                key=lambda x: x[1]['max_ratio'],
                reverse=True
            )[:15]
            
            for rank, (interest, info) in enumerate(sorted_interests, 1):
                tables_html += f'''
                    <tr>
                        <td>{rank}</td>
                        <td><strong>{interest}</strong></td>
                        <td>{info['count']}</td>
                        <td>{info['max_ratio']:.2f}x</td>
                        <td>{', '.join(info['clusters'][:3])}</td>
                    </tr>'''
            
            tables_html += '''
                </tbody>
            </table>
        </div>'''
        
        # 3. 独特属性排名表格
        all_unique_attributes = {}
        for cluster in clusters:
            for attr in cluster.get('uniqueness', {}).get('unique_attributes', []):
                attr_name = attr.get('attribute', '')
                if attr_name:
                    if attr_name not in all_unique_attributes:
                        all_unique_attributes[attr_name] = {
                            'count': 0,
                            'max_ratio': 0,
                            'clusters': []
                        }
                    all_unique_attributes[attr_name]['count'] += 1
                    ratio = attr.get('uniqueness_ratio', 0)
                    if ratio > all_unique_attributes[attr_name]['max_ratio']:
                        all_unique_attributes[attr_name]['max_ratio'] = ratio
                    all_unique_attributes[attr_name]['clusters'].append(cluster.get('cluster_id', ''))
        
        if all_unique_attributes:
            tables_html += '''
        <div class="section">
            <h2>独特属性排名（按独特性倍数）</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>属性</th>
                        <th>出现聚类数</th>
                        <th>最高独特性倍数</th>
                        <th>相关聚类</th>
                    </tr>
                </thead>
                <tbody>'''
            
            sorted_attrs = sorted(
                all_unique_attributes.items(),
                key=lambda x: x[1]['max_ratio'],
                reverse=True
            )[:15]
            
            for rank, (attr, info) in enumerate(sorted_attrs, 1):
                tables_html += f'''
                    <tr>
                        <td>{rank}</td>
                        <td><strong>{attr}</strong></td>
                        <td>{info['count']}</td>
                        <td>{info['max_ratio']:.2f}x</td>
                        <td>{', '.join(info['clusters'][:3])}</td>
                    </tr>'''
            
            tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 插入表格
    if tables_html:
        pattern = r'(<div class="section">)'
        if re.search(pattern, html_content):
            html_content = re.sub(
                pattern,
                tables_html + r'\1',
                html_content,
                count=1
            )
        else:
            html_content = re.sub(
                r'(<div id="content">)',
                r'\1' + tables_html,
                html_content
            )
    
    return html_content

def add_tables_to_bounce_user_dashboard(html_content, data_file):
    """为跳出用户分析Dashboard添加表格"""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取数据文件失败: {e}")
        return html_content
    
    tables_html = ''
    
    # 1. 行为统计表格 - 兴趣排名
    if 'behavior_statistics' in data and 'top_interests' in data['behavior_statistics']:
        interests = data['behavior_statistics']['top_interests']
        tables_html += '''
        <div class="section">
            <h2>5秒跳出用户 - 兴趣排名</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>兴趣</th>
                        <th>出现次数</th>
                        <th>占比</th>
                    </tr>
                </thead>
                <tbody>'''
        
        sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:15]
        total = sum(interests.values())
        
        for rank, (interest, count) in enumerate(sorted_interests, 1):
            pct = (count / total * 100) if total > 0 else 0
            tables_html += f'''
                    <tr>
                        <td>{rank}</td>
                        <td><strong>{interest}</strong></td>
                        <td>{count}</td>
                        <td>{pct:.1f}%</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 2. 购买阶段分布表格
    if 'behavior_statistics' in data and 'top_stages' in data['behavior_statistics']:
        stages = data['behavior_statistics']['top_stages']
        tables_html += '''
        <div class="section">
            <h2>5秒跳出用户 - 购买阶段分布</h2>
            <table>
                <thead>
                    <tr>
                        <th>购买阶段</th>
                        <th>用户数</th>
                        <th>占比</th>
                        <th>说明</th>
                    </tr>
                </thead>
                <tbody>'''
        
        sorted_stages = sorted(stages.items(), key=lambda x: x[1], reverse=True)
        total = sum(stages.values())
        
        stage_descriptions = {
            'browsing': '浏览阶段 - 初步了解产品',
            'comparing': '对比阶段 - 比较不同产品',
            'deciding': '决策阶段 - 准备购买',
            'browsing/comparing': '浏览/对比阶段'
        }
        
        for stage, count in sorted_stages:
            pct = (count / total * 100) if total > 0 else 0
            desc = stage_descriptions.get(stage, '其他阶段')
            tables_html += f'''
                    <tr>
                        <td><strong>{stage}</strong></td>
                        <td>{count}</td>
                        <td>{pct:.1f}%</td>
                        <td>{desc}</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 3. 价格敏感度分布表格
    if 'behavior_statistics' in data and 'top_price_ranges' in data['behavior_statistics']:
        price_ranges = data['behavior_statistics']['top_price_ranges']
        tables_html += '''
        <div class="section">
            <h2>5秒跳出用户 - 价格敏感度分布</h2>
            <table>
                <thead>
                    <tr>
                        <th>价格区间</th>
                        <th>用户数</th>
                        <th>占比</th>
                        <th>说明</th>
                    </tr>
                </thead>
                <tbody>'''
        
        sorted_prices = sorted(price_ranges.items(), key=lambda x: x[1], reverse=True)
        total = sum(price_ranges.values())
        
        price_descriptions = {
            'premium': '高端 - 注重品质和功能',
            'mid-range': '中端 - 性价比平衡',
            'budget': '预算型 - 价格敏感'
        }
        
        for price_range, count in sorted_prices:
            pct = (count / total * 100) if total > 0 else 0
            desc = price_descriptions.get(price_range, '其他')
            tables_html += f'''
                    <tr>
                        <td><strong>{price_range}</strong></td>
                        <td>{count}</td>
                        <td>{pct:.1f}%</td>
                        <td>{desc}</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 4. 跳出原因置信度表格
    if 'gemini_analysis' in data and 'bounce_reasons' in data['gemini_analysis']:
        reasons = data['gemini_analysis']['bounce_reasons']
        tables_html += '''
        <div class="section">
            <h2>跳出原因分析（按置信度排序）</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>跳出原因</th>
                        <th>置信度</th>
                        <th>关键证据</th>
                    </tr>
                </thead>
                <tbody>'''
        
        sorted_reasons = sorted(reasons, key=lambda x: x.get('confidence', 0), reverse=True)
        
        for rank, reason in enumerate(sorted_reasons, 1):
            reason_text = reason.get('reason', '')
            confidence = reason.get('confidence', 0)
            evidence = reason.get('evidence', '')
            # 截断过长的证据
            if len(evidence) > 150:
                evidence = evidence[:150] + '...'
            
            tables_html += f'''
                    <tr>
                        <td>{rank}</td>
                        <td><strong>{reason_text}</strong></td>
                        <td>{confidence * 100:.0f}%</td>
                        <td>{evidence}</td>
                    </tr>'''
        
        tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 插入表格
    if tables_html:
        pattern = r'(<div class="section">)'
        if re.search(pattern, html_content):
            html_content = re.sub(
                pattern,
                tables_html + r'\1',
                html_content,
                count=1
            )
        else:
            html_content = re.sub(
                r'(<div id="content">)',
                r'\1' + tables_html,
                html_content
            )
    
    return html_content

def main():
    """主函数"""
    base_dir = Path('.')
    
    dashboards = [
        ('core_users_comparison_dashboard.html', '../../results/analysis/core_users_10_60s_analysis.json', add_tables_to_core_users_dashboard),
        ('cluster_specific_dashboard_enhanced.html', '../../results/clustering/cluster_specific_analysis_enhanced.json', add_tables_to_cluster_specific_dashboard),
        ('bounce_user_dashboard.html', '../../results/analysis/bounce_user_analysis.json', add_tables_to_bounce_user_dashboard),
    ]
    
    print("为Dashboard添加表格来直观展现结论...\n")
    
    for html_file, data_file, add_tables_func in dashboards:
        html_path = base_dir / html_file
        data_path = Path(data_file)
        
        if html_path.exists() and data_path.exists():
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = add_tables_func(content, data_path)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ {html_file}")
            except Exception as e:
                print(f"❌ {html_file}: {e}")
        else:
            missing = []
            if not html_path.exists():
                missing.append(html_file)
            if not data_path.exists():
                missing.append(data_file)
            print(f"⚠️ 文件不存在: {', '.join(missing)}")
    
    print("\n✅ 所有表格已添加完成！")

if __name__ == '__main__':
    main()

