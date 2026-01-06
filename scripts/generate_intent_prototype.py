#!/usr/bin/env python3
"""
根据聚类结果生成商家的长期数字资产Intent Prototype
参考源数据中的Metadata部分
增加相似度分析和合并机制，确保每个prototype具有极高区分度
"""
import json
import csv
import sys
from typing import Dict, List, Set, Tuple
from collections import Counter
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

csv.field_size_limit(sys.maxsize)


def load_cluster_results(results_file: str) -> Dict:
    """加载聚类结果"""
    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_metadata_info(csv_file: str, sample_ids: List[str]) -> Dict:
    """从CSV中提取样本的Metadata信息"""
    metadata_info = {
        'shop_ids': set(),
        'shop_types': set(),
        'all_tags': [],
        'shop_info_samples': []
    }
    
    id_set = set(sample_ids)
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_id = row.get('id', '').strip('"')
                if row_id in id_set:
                    metadata = row.get('metadata', '')
                    if metadata:
                        try:
                            meta_json = json.loads(metadata)
                            
                            # 提取shop信息
                            if 'shop_id' in meta_json:
                                metadata_info['shop_ids'].add(meta_json['shop_id'])
                            if 'shop_type' in meta_json:
                                metadata_info['shop_types'].add(meta_json['shop_type'])
                            
                            # 提取tags
                            if 'tags' in meta_json:
                                tags_str = meta_json['tags']
                                if isinstance(tags_str, str):
                                    try:
                                        tags = json.loads(tags_str)
                                        if isinstance(tags, list):
                                            metadata_info['all_tags'].extend(tags)
                                    except:
                                        pass
                            
                            # 提取shop_info
                            if 'shop_info' in meta_json:
                                shop_info_str = meta_json['shop_info']
                                if isinstance(shop_info_str, str):
                                    try:
                                        shop_info = json.loads(shop_info_str)
                                        if shop_info:
                                            metadata_info['shop_info_samples'].append(shop_info)
                                    except:
                                        pass
                        except:
                            pass
    except Exception as e:
        print(f"警告: 读取Metadata时出错: {e}")
    
    return metadata_info


def generate_intent_prototype(cluster: Dict, metadata_info: Dict, cluster_id: int) -> Dict:
    """为单个聚类生成Intent Prototype"""
    
    # 提取最频繁的tags
    tag_counter = Counter(metadata_info['all_tags'])
    top_tags = [tag for tag, count in tag_counter.most_common(20)]
    
    # 清理summary文本
    summary = cluster.get('summary', '').replace('**聚类摘要：**', '').replace('**', '').strip()
    
    # 从summary中提取关键信息
    summary_lines = summary.split('\n')
    main_description = summary_lines[0] if summary_lines else summary
    
    prototype = {
        'intent_cluster_id': cluster_id,
        'cluster_size': cluster.get('size', 0),
        'intent_description': {
            'summary': main_description,
            'full_summary': summary
        },
        'user_intent_characteristics': {
            'primary_interests': extract_key_phrases(summary),
            'user_behavior_patterns': analyze_behavior_patterns(cluster),
            'intent_strength': 'high' if cluster.get('size', 0) > 100 else 'medium' if cluster.get('size', 0) > 50 else 'low'
        },
        'product_alignment': {
            'relevant_tags': top_tags,
            'product_categories': extract_categories(summary, top_tags),
            'key_product_attributes': extract_attributes(summary)
        },
        'shop_context': {
            'shop_ids': list(metadata_info['shop_ids']),
            'shop_types': list(metadata_info['shop_types']),
            'shop_count': len(metadata_info['shop_ids'])
        },
        'marketing_insights': {
            'target_audience': infer_target_audience(summary),
            'content_strategy': generate_content_strategy(summary, top_tags),
            'conversion_opportunities': identify_conversion_opportunities(cluster)
        },
        'long_term_value': {
            'asset_type': 'user_intent_prototype',
            'update_frequency': 'monthly',
            'applicable_channels': ['search', 'recommendation', 'personalization', 'content_marketing'],
            'data_sources': ['user_behavior', 'search_queries', 'product_interactions']
        }
    }
    
    return prototype


def extract_key_phrases(text: str) -> List[str]:
    """从文本中提取关键短语，优先提取独特的、有区分度的短语"""
    key_phrases = []
    
    # 提取加粗或引号中的内容（这些通常是强调的重点）
    import re
    bold_pattern = r'\*\*([^*]+)\*\*'
    quotes_pattern = r'["""]([^"""]+)["""]'
    
    for pattern in [bold_pattern, quotes_pattern]:
        matches = re.findall(pattern, text)
        key_phrases.extend(matches)
    
    # 优先提取有区分度的关键词（避免过于通用的词）
    # 高区分度关键词（这些词更能区分不同聚类）
    high_distinct_keywords = ['订单', '账户', '登录', '追踪', '心跳', '呼吸', '声音', '互动', 
                              '收藏', '配件', '尺寸', '性别', '眼睛', '头发', '材质', '全身硅胶',
                              '布身', '乙烯基', '重生', '写实', '仿真']
    
    # 低区分度关键词（这些词太通用，尽量避免）
    low_distinct_keywords = ['逼真', '婴儿', '娃娃', '硅胶', 'doll', 'baby']
    
    # 优先提取高区分度关键词
    for keyword in high_distinct_keywords:
        if keyword in text and keyword not in key_phrases:
            key_phrases.append(keyword)
    
    # 如果高区分度关键词不够，再添加一些低区分度的
    if len(key_phrases) < 5:
        for keyword in low_distinct_keywords:
            if keyword in text and keyword not in key_phrases:
                key_phrases.append(keyword)
                if len(key_phrases) >= 10:
                    break
    
    return list(set(key_phrases))[:10]


def analyze_behavior_patterns(cluster: Dict) -> List[str]:
    """分析用户行为模式，强调独特的、有区分度的模式"""
    patterns = []
    size = cluster.get('size', 0)
    summary = cluster.get('summary', '').lower()
    
    # 优先识别独特的行为模式（这些更能区分不同聚类）
    if '订单' in summary or 'order' in summary or 'tracking' in summary:
        if '查询' in summary or '查询' in cluster.get('summary', ''):
            patterns.append('订单查询与追踪需求')
        else:
            patterns.append('订单管理相关意图')
    elif '账户' in summary or 'account' in summary or 'login' in summary or '登录' in summary:
        patterns.append('账户管理与登录需求')
    elif '互动' in summary or 'interactive' in summary or '心跳' in summary or 'heartbeat' in summary:
        patterns.append('互动功能探索行为')
    elif '收藏' in summary or 'collectible' in summary:
        patterns.append('收藏价值导向')
    elif '配件' in summary or 'accessories' in summary:
        patterns.append('配件需求明确')
    elif '搜索' in summary or '查询' in summary:
        patterns.append('主动搜索行为')
    elif '购买' in summary or 'buy' in summary:
        patterns.append('购买意向明确')
    else:
        patterns.append('信息收集阶段')
    
    # 添加规模信息（作为补充）
    if size > 200:
        patterns.append('高流量意图群体')
    elif size > 100:
        patterns.append('中等流量意图群体')
    else:
        patterns.append('细分意图群体')
    
    return patterns


def extract_categories(summary: str, tags: List[str]) -> List[str]:
    """提取产品类别"""
    categories = []
    
    summary_lower = summary.lower()
    
    if '硅胶' in summary or 'silicone' in summary_lower:
        categories.append('硅胶婴儿娃娃')
    if '重生' in summary or 'reborn' in summary_lower:
        categories.append('重生婴儿娃娃')
    if '收藏' in summary or 'collectible' in summary_lower:
        categories.append('收藏级娃娃')
    if '配件' in summary or 'accessories' in summary_lower:
        categories.append('娃娃配件')
    
    # 从tags中提取
    for tag in tags[:10]:
        if any(keyword in tag.lower() for keyword in ['doll', 'baby', 'toy', 'collectible']):
            categories.append(tag)
    
    return list(set(categories))[:10]


def extract_attributes(summary: str) -> List[str]:
    """提取关键产品属性"""
    attributes = []
    
    attribute_keywords = {
        '尺寸': ['尺寸', 'size', '12', '16', '20', 'inch'],
        '材质': ['材质', 'material', '硅胶', 'silicone', 'vinyl', 'cloth'],
        '功能': ['心跳', 'heartbeat', '呼吸', 'breath', '声音', 'sound', '互动', 'interactive'],
        '外观': ['眼睛', 'eye', '头发', 'hair', '肤色', 'skin'],
        '性别': ['性别', 'gender', 'boy', 'girl', '男孩', '女孩']
    }
    
    summary_lower = summary.lower()
    for attr_name, keywords in attribute_keywords.items():
        if any(kw in summary or kw.lower() in summary_lower for kw in keywords):
            attributes.append(attr_name)
    
    return attributes


def infer_target_audience(summary: str) -> List[str]:
    """推断目标受众"""
    audience = []
    
    summary_lower = summary.lower()
    
    if '收藏' in summary or 'collector' in summary_lower:
        audience.append('收藏家')
    if '儿童' in summary or 'kids' in summary_lower or 'children' in summary_lower:
        audience.append('儿童家长')
    if '礼物' in summary or 'gift' in summary_lower:
        audience.append('礼品购买者')
    if '账户' in summary or '订单' in summary or 'account' in summary_lower or 'order' in summary_lower:
        audience.append('现有客户')
    
    if not audience:
        audience.append('对逼真婴儿娃娃感兴趣的消费者')
    
    return audience


def generate_content_strategy(summary: str, tags: List[str]) -> List[str]:
    """生成内容策略建议"""
    strategies = []
    
    summary_lower = summary.lower()
    
    if '搜索' in summary or '查询' in summary:
        strategies.append('优化SEO关键词，匹配用户搜索意图')
    
    if '细节' in summary or '特征' in summary or 'detail' in summary_lower:
        strategies.append('突出产品细节和特征的高质量内容')
    
    if '互动' in summary or '功能' in summary or 'interactive' in summary_lower:
        strategies.append('展示产品互动功能的视频和图片')
    
    if '收藏' in summary or 'collectible' in summary_lower:
        strategies.append('强调收藏价值和限量版特性')
    
    # 基于tags的策略
    if tags:
        strategies.append(f'使用相关标签: {", ".join(tags[:5])}')
    
    return strategies


def identify_conversion_opportunities(cluster: Dict) -> List[str]:
    """识别转化机会"""
    opportunities = []
    
    size = cluster.get('size', 0)
    summary = cluster.get('summary', '').lower()
    
    if size > 100:
        opportunities.append('高流量意图，适合投放广告和促销活动')
    
    if '购买' in summary or '订单' in summary or 'buy' in summary or 'order' in summary:
        opportunities.append('购买意向明确，可提供快速购买路径')
    
    if '详情' in summary or '规格' in summary or 'detail' in summary or 'specification' in summary:
        opportunities.append('信息需求强烈，提供详细产品页面')
    
    if '比较' in summary or '对比' in summary or 'compare' in summary:
        opportunities.append('对比需求，提供产品对比工具')
    
    return opportunities


def load_cluster_embeddings(embeddings_file: str, cluster_results: Dict) -> Dict[int, np.ndarray]:
    """加载每个聚类的平均embedding向量"""
    print("加载聚类embedding数据...")
    
    # 加载embedding数据
    with open(embeddings_file, 'r', encoding='utf-8') as f:
        embedding_data = json.load(f)
    
    # 创建id到embedding的映射
    id_to_embedding = {}
    for item in embedding_data:
        if item.get('embedding') is not None:
            item_id = item['id'].strip('"')
            id_to_embedding[item_id] = np.array(item['embedding'])
    
    # 为每个聚类计算平均embedding
    cluster_embeddings = {}
    for cluster in cluster_results['cluster_summaries']:
        cluster_id = cluster['cluster_id']
        sample_ids = [sample['id'].strip('"') for sample in cluster.get('top_samples', [])]
        
        # 获取这些样本的embedding
        sample_embeddings = []
        for sample_id in sample_ids:
            if sample_id in id_to_embedding:
                sample_embeddings.append(id_to_embedding[sample_id])
        
        if sample_embeddings:
            # 计算平均embedding并归一化
            avg_embedding = np.mean(sample_embeddings, axis=0)
            norm = np.linalg.norm(avg_embedding)
            if norm > 0:
                avg_embedding = avg_embedding / norm
            cluster_embeddings[cluster_id] = avg_embedding
    
    print(f"加载了 {len(cluster_embeddings)} 个聚类的embedding")
    return cluster_embeddings


def calculate_cluster_similarity(cluster_embeddings: Dict[int, np.ndarray], 
                                similarity_threshold: float = 0.85) -> List[Set[int]]:
    """计算聚类之间的相似度，返回需要合并的聚类组"""
    print(f"\n分析聚类相似度（阈值: {similarity_threshold}）...")
    
    cluster_ids = sorted(cluster_embeddings.keys())
    n_clusters = len(cluster_ids)
    
    # 计算相似度矩阵
    similarity_matrix = np.zeros((n_clusters, n_clusters))
    for i, id1 in enumerate(cluster_ids):
        for j, id2 in enumerate(cluster_ids):
            if i == j:
                similarity_matrix[i][j] = 1.0
            else:
                emb1 = cluster_embeddings[id1]
                emb2 = cluster_embeddings[id2]
                similarity = cosine_similarity([emb1], [emb2])[0][0]
                similarity_matrix[i][j] = similarity
    
    # 打印相似度统计信息
    similarities_above_threshold = []
    for i, id1 in enumerate(cluster_ids):
        for j, id2 in enumerate(cluster_ids):
            if i < j:  # 只计算上三角矩阵，避免重复
                sim = similarity_matrix[i][j]
                if sim >= similarity_threshold:
                    similarities_above_threshold.append((id1, id2, sim))
    
    if similarities_above_threshold:
        print(f"  发现 {len(similarities_above_threshold)} 对相似聚类（相似度 >= {similarity_threshold}）:")
        for id1, id2, sim in sorted(similarities_above_threshold, key=lambda x: x[2], reverse=True)[:10]:
            print(f"    聚类 {id1} <-> 聚类 {id2}: {sim:.4f}")
    else:
        print(f"  未发现相似度 >= {similarity_threshold} 的聚类对")
    
    # 找出需要合并的聚类组
    merged_groups = []
    processed = set()
    
    for i, id1 in enumerate(cluster_ids):
        if id1 in processed:
            continue
        
        # 找到与id1高度相似的聚类
        similar_clusters = {id1}
        for j, id2 in enumerate(cluster_ids):
            if i != j and id2 not in processed:
                if similarity_matrix[i][j] >= similarity_threshold:
                    similar_clusters.add(id2)
                    processed.add(id2)
        
        if len(similar_clusters) > 1:
            merged_groups.append(similar_clusters)
            # 显示合并的聚类及其相似度
            group_list = sorted(list(similar_clusters))
            sim_values = []
            for idx1, cid1 in enumerate(group_list):
                for idx2, cid2 in enumerate(group_list):
                    if idx1 < idx2:
                        pos1 = cluster_ids.index(cid1)
                        pos2 = cluster_ids.index(cid2)
                        sim_values.append(similarity_matrix[pos1][pos2])
            avg_sim = np.mean(sim_values) if sim_values else 0
            print(f"  合并聚类组: {group_list} (平均相似度: {avg_sim:.4f})")
        else:
            # 单独保留的聚类
            merged_groups.append(similar_clusters)
        
        processed.add(id1)
    
    print(f"合并后共有 {len(merged_groups)} 个独特的prototype")
    return merged_groups


def merge_clusters(cluster_results: Dict, merged_groups: List[Set[int]]) -> List[Dict]:
    """合并高度相似的聚类"""
    print("\n合并相似聚类...")
    
    merged_clusters = []
    
    for group in merged_groups:
        group_list = sorted(list(group))
        
        if len(group_list) == 1:
            # 单独保留
            cluster_id = group_list[0]
            original_cluster = next(c for c in cluster_results['cluster_summaries'] 
                                   if c['cluster_id'] == cluster_id)
            merged_clusters.append({
                'merged_cluster_ids': [cluster_id],
                'cluster_id': cluster_id,
                'size': original_cluster['size'],
                'top_samples': original_cluster['top_samples'],
                'summary': original_cluster['summary']
            })
        else:
            # 合并多个聚类
            merged_size = 0
            all_top_samples = []
            all_summaries = []
            
            for cluster_id in group_list:
                original_cluster = next(c for c in cluster_results['cluster_summaries'] 
                                      if c['cluster_id'] == cluster_id)
                merged_size += original_cluster['size']
                all_top_samples.extend(original_cluster['top_samples'])
                all_summaries.append(original_cluster['summary'])
            
            # 合并摘要（取最长的或最详细的）
            merged_summary = max(all_summaries, key=len)
            
            # 去重top_samples（保留前10个）
            seen_ids = set()
            unique_samples = []
            for sample in all_top_samples:
                sample_id = sample['id'].strip('"')
                if sample_id not in seen_ids:
                    unique_samples.append(sample)
                    seen_ids.add(sample_id)
                    if len(unique_samples) >= 10:
                        break
            
            merged_clusters.append({
                'merged_cluster_ids': group_list,
                'cluster_id': group_list[0],  # 使用第一个ID作为主ID
                'size': merged_size,
                'top_samples': unique_samples,
                'summary': merged_summary
            })
            print(f"  合并聚类 {group_list} -> 新聚类 {group_list[0]} (总样本数: {merged_size})")
    
    return merged_clusters


def should_keep_prototype(cluster: Dict) -> bool:
    """
    判断是否应该保留这个prototype
    只保留从浏览到下单阶段的prototype，排除账户、订单和设置相关的
    """
    summary = cluster.get('summary', '').lower()
    
    # 排除关键词：账户相关（更精确的匹配）
    account_keywords = [
        '账户管理', 'account management', '登录/密码', 'login/password', 
        'password reset', '密码重置', '账户安全', 'account security',
        '账户访问', 'account access', '账户历史', 'account history'
    ]
    
    # 排除关键词：订单相关（订单查询、追踪、管理，但排除购买相关的）
    order_keywords = [
        '订单查询', 'order query', '订单追踪', 'order tracking', 
        '订单管理', 'order management', '查单', '查询订单', 
        '订单状态', 'order status', '配送状态', 'delivery status',
        '交易生命周期', 'transaction lifecycle', '订单的生命周期',
        '既有订单', 'existing order', 'past purchases', '历史购买',
        '购买后跟进', 'post-purchase', '售后', 'after-sale'
    ]
    
    # 排除关键词：设置相关
    setting_keywords = [
        '个人设置', 'personal setting', '账户设置', 'account setting',
        '偏好设置', 'preference setting'
    ]
    
    # 检查是否主要关注排除的关键词（需要更精确的判断）
    # 如果summary中明确提到这些是"核心关注点"或"主要意图"，则排除
    exclude_phrases = [
        '核心关注点在于', '主要关注点', '核心驱动力', '核心需求',
        '意图明确指向', '意图高度聚焦于', '专注于'
    ]
    
    # 检查是否包含排除关键词，并且这些关键词是主要关注点
    all_exclude_keywords = account_keywords + order_keywords + setting_keywords
    for keyword in all_exclude_keywords:
        if keyword in summary:
            # 检查这个关键词是否在summary中作为主要关注点出现
            keyword_pos = summary.find(keyword)
            # 检查关键词前后是否有排除短语
            context_start = max(0, keyword_pos - 50)
            context_end = min(len(summary), keyword_pos + len(keyword) + 50)
            context = summary[context_start:context_end]
            
            # 如果上下文中包含排除短语，说明这是主要关注点，应该排除
            for phrase in exclude_phrases:
                if phrase in context:
                    return False
            
            # 如果关键词本身就很明确（如"账户管理"、"订单追踪"），直接排除
            if any(kw in keyword for kw in ['管理', 'management', '追踪', 'tracking', '查询', 'query']):
                return False
    
    # 如果通过了排除检查，则保留
    return True


def main():
    # 文件路径
    cluster_results_file = "../results/cluster_results.json"
    csv_file = "../data/ikarao.csv"
    embeddings_file = "../data/output_embeddings.json"
    output_file = "../results/intent_prototypes.json"
    similarity_threshold = 0.98  # 相似度阈值，提高到0.98只合并几乎完全相同的聚类，保留更多独立的prototype
    
    print("="*70)
    print("Intent Prototype 生成（带相似度分析和合并）")
    print("="*70)
    
    print("\n1. 加载聚类结果...")
    cluster_results = load_cluster_results(cluster_results_file)
    original_count = len(cluster_results['cluster_summaries'])
    print(f"   原始聚类数: {original_count}")
    
    # 先过滤掉账户、订单、设置相关的聚类（在合并之前）
    print("\n2. 预过滤聚类（只保留从浏览到下单阶段的prototype）...")
    print("="*70)
    filtered_cluster_results = {
        'cluster_summaries': [],
        'total_samples': cluster_results.get('total_samples', 0),
        'optimal_k': cluster_results.get('optimal_k', 0),
        'k_selection_results': cluster_results.get('k_selection_results', {})
    }
    
    pre_filtered_count = 0
    for cluster in cluster_results['cluster_summaries']:
        if should_keep_prototype(cluster):
            filtered_cluster_results['cluster_summaries'].append(cluster)
        else:
            cluster_id = cluster['cluster_id']
            summary_preview = cluster.get('summary', '')[:80].replace('\n', ' ')
            print(f"  预过滤掉聚类 {cluster_id}: {summary_preview}...")
            pre_filtered_count += 1
    
    print(f"\n   保留聚类数: {len(filtered_cluster_results['cluster_summaries'])}")
    print(f"   预过滤掉聚类数: {pre_filtered_count}")
    
    # 加载embedding并计算相似度（只对过滤后的聚类）
    if os.path.exists(embeddings_file):
        print("\n3. 分析聚类相似度...")
        cluster_embeddings = load_cluster_embeddings(embeddings_file, filtered_cluster_results)
        
        if cluster_embeddings:
            merged_groups = calculate_cluster_similarity(cluster_embeddings, similarity_threshold)
            merged_clusters = merge_clusters(filtered_cluster_results, merged_groups)
        else:
            print("   警告: 无法加载embedding，跳过合并步骤")
            merged_clusters = [{
                'merged_cluster_ids': [c['cluster_id']],
                'cluster_id': c['cluster_id'],
                'size': c['size'],
                'top_samples': c['top_samples'],
                'summary': c['summary']
            } for c in filtered_cluster_results['cluster_summaries']]
    else:
        print("   警告: embedding文件不存在，跳过相似度分析")
        merged_clusters = [{
            'merged_cluster_ids': [c['cluster_id']],
            'cluster_id': c['cluster_id'],
            'size': c['size'],
            'top_samples': c['top_samples'],
            'summary': c['summary']
        } for c in filtered_cluster_results['cluster_summaries']]
    
    print(f"\n4. 生成Intent Prototype（合并后: {len(merged_clusters)} 个）...")
    print("="*70)
    
    prototypes = []
    
    for merged_cluster in merged_clusters:
        cluster_id = merged_cluster['cluster_id']
        merged_ids = merged_cluster['merged_cluster_ids']
        
        if len(merged_ids) > 1:
            print(f"\n处理合并聚类 {merged_ids} -> {cluster_id}...")
        else:
            print(f"\n处理聚类 {cluster_id}...")
        
        # 提取所有样本ID
        sample_ids = [sample['id'] for sample in merged_cluster.get('top_samples', [])]
        
        # 提取Metadata信息
        print(f"  提取Metadata信息...")
        metadata_info = extract_metadata_info(csv_file, sample_ids)
        
        # 生成Intent Prototype
        print(f"  生成Intent Prototype...")
        prototype = generate_intent_prototype(merged_cluster, metadata_info, cluster_id)
        
        # 添加合并信息
        if len(merged_ids) > 1:
            prototype['merged_from_clusters'] = merged_ids
            prototype['is_merged'] = True
        else:
            prototype['is_merged'] = False
        
        prototypes.append(prototype)
        
        print(f"  ✓ 完成")
    
    # 保存结果
    output_data = {
        'metadata': {
            'generation_date': __import__('datetime').datetime.now().isoformat(),
            'original_cluster_count': original_count,
            'pre_filtered_count': pre_filtered_count,
            'clusters_after_prefilter': len(filtered_cluster_results['cluster_summaries']),
            'final_prototype_count': len(prototypes),
            'merged_count': sum(1 for p in prototypes if p.get('is_merged', False)),
            'total_samples': cluster_results.get('total_samples', 0),
            'optimal_k': cluster_results.get('optimal_k', 0),
            'similarity_threshold': similarity_threshold
        },
        'intent_prototypes': prototypes
    }
    
    print(f"\n5. 保存结果...")
    print(f"   保存到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("完成！")
    print("="*70)
    print(f"原始聚类数: {original_count}")
    print(f"预过滤掉聚类数: {pre_filtered_count}")
    print(f"预过滤后聚类数: {len(filtered_cluster_results['cluster_summaries'])}")
    print(f"最终Prototype数: {len(prototypes)}")
    print(f"合并的Prototype数: {sum(1 for p in prototypes if p.get('is_merged', False))}")
    print(f"独立保留的Prototype数: {sum(1 for p in prototypes if not p.get('is_merged', False))}")
    
    # 打印摘要
    print("\n" + "="*70)
    print("Intent Prototype 摘要:")
    print("="*70)
    for proto in prototypes:
        cluster_id = proto['intent_cluster_id']
        merged_info = ""
        if proto.get('is_merged', False):
            merged_ids = proto.get('merged_from_clusters', [])
            merged_info = f" [合并自: {merged_ids}]"
        
        print(f"\nPrototype {cluster_id}{merged_info} ({proto['cluster_size']}个样本):")
        print(f"  意图: {proto['intent_description']['summary'][:100]}...")
        print(f"  主要兴趣: {', '.join(proto['user_intent_characteristics']['primary_interests'][:5])}")
        print(f"  目标受众: {', '.join(proto['marketing_insights']['target_audience'])}")


if __name__ == "__main__":
    main()

