#!/usr/bin/env python3
"""
对CSV文件中的两个聚类进行详细分析
"""
import json
import csv
import sys
import os
from typing import Dict, List
from collections import Counter

# 增加CSV字段大小限制
csv.field_size_limit(sys.maxsize)

try:
    import google.generativeai as genai
except ImportError:
    print("请先安装google-generativeai: pip install google-generativeai")
    sys.exit(1)


def load_api_key() -> str:
    """从环境变量或用户输入获取API key"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = input("请输入您的Gemini API Key: ").strip()
        if not api_key:
            raise ValueError("需要提供Gemini API Key")
    return api_key


def load_csv_data(csv_file: str) -> List[Dict]:
    """加载CSV数据"""
    print(f"加载CSV数据: {csv_file}")
    data = []
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        print(f"加载了 {len(data)} 条数据")
    except Exception as e:
        print(f"错误: 无法加载CSV文件 {csv_file}: {e}")
        sys.exit(1)
    return data


def analyze_cluster(cluster_data: List[Dict], cluster_id: str) -> Dict:
    """分析单个聚类"""
    print(f"\n分析聚类 {cluster_id} ({len(cluster_data)} 条数据)...")
    
    # 提取所有summary
    summaries = []
    core_interests_all = []
    product_focus_all = []
    behavior_patterns = []
    shop_ids = []
    
    for item in cluster_data:
        summary_str = item.get('summary', '')
        if summary_str:
            try:
                summary_json = json.loads(summary_str)
                summaries.append(summary_json)
                
                # 提取核心兴趣
                if 'core_interests' in summary_json:
                    core_interests_all.extend(summary_json['core_interests'])
                
                # 提取产品焦点
                if 'product_focus' in summary_json:
                    product_focus = summary_json['product_focus']
                    if 'key_attributes' in product_focus:
                        product_focus_all.extend(product_focus['key_attributes'])
                
                # 提取行为模式
                if 'behavior_summary' in summary_json:
                    behavior_patterns.append(summary_json['behavior_summary'])
                
                # 提取shop_id
                shop_id = item.get('shop_id', '')
                if shop_id:
                    shop_ids.append(shop_id)
                    
            except json.JSONDecodeError:
                print(f"警告: 无法解析ID {item.get('id')} 的summary")
    
    # 统计最频繁的核心兴趣
    interest_counter = Counter(core_interests_all)
    top_interests = interest_counter.most_common(10)
    
    # 统计最频繁的产品属性
    attribute_counter = Counter(product_focus_all)
    top_attributes = attribute_counter.most_common(10)
    
    # 统计shop分布
    shop_counter = Counter(shop_ids)
    top_shops = shop_counter.most_common(5)
    
    # 分析行为模式
    engagement_levels = []
    purchase_stages = []
    for behavior in behavior_patterns:
        if 'engagement' in behavior:
            engagement_levels.append(behavior['engagement'])
        if 'purchase_signals' in summaries[0] if summaries else False:
            purchase_signal = summaries[0].get('purchase_signals', {})
            if 'stage' in purchase_signal:
                purchase_stages.append(purchase_signal['stage'])
    
    return {
        'cluster_id': cluster_id,
        'size': len(cluster_data),
        'top_interests': top_interests,
        'top_attributes': top_attributes,
        'top_shops': top_shops,
        'engagement_levels': list(set(engagement_levels)),
        'purchase_stages': list(set(purchase_stages)),
        'sample_summaries': summaries[:3]  # 保存前3个样本作为示例
    }


def generate_cluster_analysis_report(cluster_analysis: Dict, model_name: str = "models/gemini-flash-lite-latest") -> str:
    """使用AI生成聚类分析报告"""
    api_key = load_api_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    # 构建分析数据摘要
    analysis_text = f"""
聚类ID: {cluster_analysis['cluster_id']}
聚类大小: {cluster_analysis['size']} 条数据

核心兴趣 (Top 10):
{chr(10).join([f"  - {interest}: {count}次" for interest, count in cluster_analysis['top_interests']])}

产品关键属性 (Top 10):
{chr(10).join([f"  - {attr}: {count}次" for attr, count in cluster_analysis['top_attributes']])}

主要店铺分布 (Top 5):
{chr(10).join([f"  - Shop {shop_id}: {count}次" for shop_id, count in cluster_analysis['top_shops']])}

参与度水平: {', '.join(cluster_analysis['engagement_levels']) if cluster_analysis['engagement_levels'] else 'N/A'}
购买阶段: {', '.join(cluster_analysis['purchase_stages']) if cluster_analysis['purchase_stages'] else 'N/A'}

示例样本摘要:
"""
    
    for i, sample in enumerate(cluster_analysis['sample_summaries'], 1):
        analysis_text += f"\n样本 {i}:\n"
        if 'core_interests' in sample:
            analysis_text += f"  核心兴趣: {', '.join(sample['core_interests'][:5])}\n"
        if 'product_focus' in sample:
            pf = sample['product_focus']
            analysis_text += f"  价格范围: {pf.get('price_range', 'N/A')}\n"
            analysis_text += f"  主要吸引力: {pf.get('main_appeal', 'N/A')}\n"
        if 'match_analysis' in sample:
            ma = sample['match_analysis']
            analysis_text += f"  用户画像: {ma.get('customer_portrait', 'N/A')}\n"
            analysis_text += f"  使用场景: {ma.get('use_case', 'N/A')}\n"
    
    prompt = f"""你是一个专业的用户行为分析专家。请基于以下聚类分析数据，生成一份详细、专业的聚类分析报告。

{analysis_text}

请生成一份包含以下内容的分析报告（使用Markdown格式）：

1. **聚类概述**
   - 聚类的基本信息和规模
   - 聚类的核心特征总结

2. **用户画像分析**
   - 基于核心兴趣和产品属性的用户特征
   - 用户行为模式和参与度分析
   - 购买意图和阶段分析

3. **产品偏好分析**
   - 最受欢迎的产品属性和特征
   - 价格敏感度分析
   - 产品吸引力因素

4. **商业洞察**
   - 目标用户群体的商业价值
   - 营销机会和建议
   - 产品推荐策略

5. **关键发现**
   - 最重要的3-5个发现
   - 值得关注的趋势或模式

请确保报告专业、详细，并且基于提供的数据进行分析。使用中文撰写。"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"生成分析报告时出错: {e}")
        return f"Error generating report: {e}"


def main():
    csv_file = "../data/intent_prototype_online.csv"
    output_dir = "../results/cluster_analysis"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*70)
    print("聚类分析工具")
    print("="*70)
    
    # 加载数据
    data = load_csv_data(csv_file)
    
    # 按cluster_hit分组
    clusters = {}
    for item in data:
        cluster_id = item.get('cluster_hit', '')
        if cluster_id:
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(item)
    
    print(f"\n发现 {len(clusters)} 个聚类:")
    for cluster_id, items in sorted(clusters.items()):
        print(f"  聚类 {cluster_id}: {len(items)} 条数据")
    
    # 分析每个聚类
    cluster_analyses = {}
    for cluster_id, cluster_data in sorted(clusters.items()):
        analysis = analyze_cluster(cluster_data, cluster_id)
        cluster_analyses[cluster_id] = analysis
    
    # 生成AI分析报告
    print("\n" + "="*70)
    print("生成AI分析报告...")
    print("="*70)
    
    reports = {}
    for cluster_id, analysis in sorted(cluster_analyses.items()):
        print(f"\n生成聚类 {cluster_id} 的分析报告...")
        report = generate_cluster_analysis_report(analysis)
        reports[cluster_id] = report
        
        # 保存单个聚类的报告
        report_file = os.path.join(output_dir, f"cluster_{cluster_id}_analysis.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 聚类 {cluster_id} 分析报告\n\n")
            f.write(f"**聚类大小**: {analysis['size']} 条数据\n\n")
            f.write("---\n\n")
            f.write(report)
        print(f"  已保存到: {report_file}")
    
    # 保存汇总数据
    summary_file = os.path.join(output_dir, "cluster_analysis_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_clusters': len(clusters),
            'cluster_analyses': cluster_analyses,
            'reports': reports
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n汇总数据已保存到: {summary_file}")
    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)


if __name__ == "__main__":
    main()

