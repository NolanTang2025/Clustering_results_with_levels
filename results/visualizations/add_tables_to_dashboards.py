#!/usr/bin/env python3
"""
为Dashboard添加表格来直观展现结论
"""

import re
import json
from pathlib import Path

def add_comparison_tables(html_content, data_file):
    """添加对比表格"""
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return html_content
    
    tables_html = ''
    
    # 如果是核心用户对比分析
    if 'comparisons' in data:
        comparisons = data['comparisons']
        
        # 兴趣对比表格
        if 'interests_comparison' in comparisons:
            interests = comparisons['interests_comparison']
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
            
            for interest, values in list(interests.items())[:10]:
                core_pct = values.get('core_pct', 0)
                other_pct = values.get('other_pct', 0)
                diff = core_pct - other_pct
                ratio = core_pct / other_pct if other_pct > 0 else 0
                
                tables_html += f'''
                    <tr>
                        <td><strong>{interest}</strong></td>
                        <td>{core_pct:.1f}%</td>
                        <td>{other_pct:.1f}%</td>
                        <td style="color: {'#1a1a1a' if diff > 0 else '#999'};">{diff:+.1f}%</td>
                        <td>{ratio:.2f}x</td>
                    </tr>'''
            
            tables_html += '''
                </tbody>
            </table>
        </div>'''
        
        # 购买阶段对比表格
        if 'stages_comparison' in comparisons:
            stages = comparisons['stages_comparison']
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
                    </tr>
                </thead>
                <tbody>'''
            
            for stage, values in stages.items():
                core_pct = values.get('core_pct', 0)
                other_pct = values.get('other_pct', 0)
                diff = core_pct - other_pct
                
                tables_html += f'''
                    <tr>
                        <td><strong>{stage}</strong></td>
                        <td>{core_pct:.1f}%</td>
                        <td>{other_pct:.1f}%</td>
                        <td style="color: {'#1a1a1a' if diff > 0 else '#999'};">{diff:+.1f}%</td>
                    </tr>'''
            
            tables_html += '''
                </tbody>
            </table>
        </div>'''
    
    # 如果是聚类特定分析
    if 'cluster_analyses' in data:
        clusters = data['cluster_analyses']
        
        # 聚类特征对比表格
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
        
        for cluster in clusters[:10]:
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
        
        # 独特特征排名表格
        all_unique_interests = {}
        all_unique_attributes = {}
        
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
    
    # 插入表格到合适位置
    if tables_html:
        # 在第一个section之前插入
        if '<div class="section">' in html_content:
            html_content = html_content.replace(
                '<div class="section">',
                tables_html + '\n        <div class="section">',
                1
            )
        else:
            # 在container内，header之后插入
            html_content = re.sub(
                r'(</div>\s*</div>\s*<div class="container">[^<]*<div class="header">[^<]*</div>)',
                r'\1' + tables_html,
                html_content,
                flags=re.DOTALL
            )
    
    return html_content

def process_dashboard(file_path, data_file=None):
    """处理单个Dashboard文件"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 根据文件名确定对应的数据文件
    if not data_file:
        file_name = file_path.name
        if 'core_users_comparison' in file_name:
            data_file = Path('../../results/analysis/core_users_10_60s_analysis.json')
        elif 'cluster_specific' in file_name:
            data_file = Path('../../results/clustering/cluster_specific_analysis_enhanced.json')
        elif 'bounce_user' in file_name:
            data_file = Path('../../results/analysis/bounce_user_analysis.json')
        else:
            return content
    
    if data_file and data_file.exists():
        content = add_comparison_tables(content, data_file)
    
    return content

def main():
    """主函数"""
    base_dir = Path('.')
    
    dashboards = [
        ('core_users_comparison_dashboard.html', '../../results/analysis/core_users_10_60s_analysis.json'),
        ('cluster_specific_dashboard_enhanced.html', '../../results/clustering/cluster_specific_analysis_enhanced.json'),
        ('bounce_user_dashboard.html', '../../results/analysis/bounce_user_analysis.json'),
    ]
    
    print("为Dashboard添加对比表格...\n")
    
    for html_file, data_file in dashboards:
        html_path = base_dir / html_file
        data_path = Path(data_file)
        
        if html_path.exists() and data_path.exists():
            try:
                new_content = process_dashboard(html_path, data_path)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ {html_file}")
            except Exception as e:
                print(f"❌ {html_file}: {e}")
        else:
            print(f"⚠️ 文件不存在: {html_file} 或 {data_file}")

if __name__ == '__main__':
    main()

