#!/usr/bin/env python3
"""
使用K-means对embedding进行聚类分析
- 使用肘部法则和轮廓系数选择最优k
- 使用MiniBatchKMeans对全量数据拟合
- 提取每个聚类最相似的10个样本
- 使用AI生成聚类摘要
"""
import json
import csv
import sys
import numpy as np
from sklearn.cluster import MiniBatchKMeans, KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import os
import time

# 增加CSV字段大小限制
csv.field_size_limit(sys.maxsize)

try:
    import google.generativeai as genai
except ImportError:
    print("请先安装google-generativeai: pip install google-generativeai")
    exit(1)


def load_full_outputs(csv_file: str) -> Dict[str, str]:
    """从原始CSV文件加载完整的output数据"""
    print(f"加载完整output数据: {csv_file}")
    output_dict = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_id = row.get('id', '').strip('"')
                output = row.get('output', '')
                if row_id and output:
                    output_dict[row_id] = output
        print(f"加载了 {len(output_dict)} 条完整output数据")
    except Exception as e:
        print(f"警告: 无法加载完整output数据: {e}")
        print("将使用embedding文件中的预览数据")
    
    return output_dict


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """对embedding向量进行L2归一化（用于余弦相似度）"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # 避免除零
    return embeddings / norms


def load_embeddings(json_file: str, full_outputs: Dict[str, str] = None) -> Tuple[np.ndarray, List[Dict]]:
    """加载embedding数据并归一化（用于余弦相似度）"""
    print(f"加载embedding数据: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 过滤掉embedding为None的数据
    valid_data = []
    for item in data:
        if item.get('embedding') is not None:
            # 如果有完整的output数据，替换预览
            if full_outputs and item.get('id'):
                item_id = item['id'].strip('"')
                if item_id in full_outputs:
                    item['output'] = full_outputs[item_id]
            valid_data.append(item)
    
    embeddings = np.array([item['embedding'] for item in valid_data])
    
    # 确保向量已归一化（如果未归一化则归一化）
    # 检查是否已归一化（归一化向量的L2范数应该接近1）
    sample_norms = np.linalg.norm(embeddings[:10], axis=1)
    if not np.allclose(sample_norms, 1.0, atol=0.01):
        print("检测到向量未归一化，正在进行L2归一化...")
        embeddings = normalize_embeddings(embeddings)
    else:
        print("向量已归一化")
    
    print(f"加载了 {len(valid_data)} 条有效embedding数据")
    print(f"Embedding维度: {embeddings.shape[1]}")
    
    return embeddings, valid_data


def find_optimal_k(embeddings: np.ndarray, k_range: range, sample_size: int = 10000) -> Dict:
    """
    使用肘部法则和轮廓系数找到最优k值
    为了加快速度，使用采样数据
    """
    print(f"\n开始寻找最优k值 (k范围: {k_range.start}-{k_range.stop-1})...")
    
    # 如果数据量太大，采样
    if len(embeddings) > sample_size:
        print(f"数据量较大，采样 {sample_size} 条数据进行k值选择...")
        indices = np.random.choice(len(embeddings), sample_size, replace=False)
        sample_embeddings = embeddings[indices]
    else:
        sample_embeddings = embeddings
    
    inertias = []
    silhouette_scores = []
    k_values = list(k_range)
    
    for k in k_values:
        print(f"  测试 k={k}...")
        
        # 使用MiniBatchKMeans快速训练
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=1000, n_init=10)
        labels = kmeans.fit_predict(sample_embeddings)
        
        inertia = kmeans.inertia_
        inertias.append(inertia)
        
        # 计算轮廓系数（可能较慢，所以采样）
        if len(sample_embeddings) > 5000:
            # 对轮廓系数计算也采样
            silhouette_sample_size = 5000
            silhouette_indices = np.random.choice(len(sample_embeddings), silhouette_sample_size, replace=False)
            silhouette_sample = sample_embeddings[silhouette_indices]
            silhouette_labels = labels[silhouette_indices]
        else:
            silhouette_sample = sample_embeddings
            silhouette_labels = labels
        
        # 使用余弦距离计算轮廓系数（向量已归一化，明确使用余弦距离）
        silhouette = silhouette_score(silhouette_sample, silhouette_labels, metric='cosine')
        silhouette_scores.append(silhouette)
        
        print(f"    k={k}: 惯性={inertia:.2f}, 轮廓系数={silhouette:.4f}")
    
    # 结合肘部法则和轮廓系数选择最优k
    # 方法：找到轮廓系数较高且惯性下降率开始变缓的k值
    
    # 计算惯性下降率
    inertia_rates = []
    for i in range(1, len(inertias)):
        if inertias[i-1] > 0:
            rate = (inertias[i-1] - inertias[i]) / inertias[i-1]
            inertia_rates.append(rate)
        else:
            inertia_rates.append(0)
    
    # 策略：排除k=2（通常太简单），在k>=3中选择
    # 1. 优先选择轮廓系数较高的k值（排除k=2）
    # 2. 同时考虑肘部法则（惯性下降率变缓的点）
    
    # 找到轮廓系数较高的候选（排除k=2，选择top 50%的k值）
    k_scores = [(k, score) for k, score in zip(k_values, silhouette_scores) if k >= 3]
    if not k_scores:
        # 如果没有k>=3的数据，至少选择k=5
        best_k = 5
    else:
        # 计算轮廓系数的中位数作为阈值
        scores_only = [score for _, score in k_scores]
        score_threshold = np.percentile(scores_only, 50)  # 选择中位数以上
        
        # 找到满足条件的k值
        candidates = [k for k, score in k_scores if score >= score_threshold]
        
        if candidates:
            # 如果有多个候选，优先选择k值在5-15之间的
            preferred_range = [k for k in candidates if 5 <= k <= 15]
            if preferred_range:
                # 在偏好范围内选择轮廓系数最高的
                best_k = max(preferred_range, 
                           key=lambda k: silhouette_scores[k_values.index(k)])
            else:
                # 如果不在偏好范围，选择最小的候选（避免过度分割）
                best_k = min(candidates)
        else:
            # 如果没有满足条件的，选择k=10（一个合理的默认值）
            best_k = 10
    
    best_k_idx = k_values.index(best_k)
    print(f"\n最优k值: {best_k} (轮廓系数: {silhouette_scores[best_k_idx]:.4f}, 惯性: {inertias[best_k_idx]:.2f})")
    print(f"选择理由: 排除k=2，在k>=3中选择轮廓系数较高的值")
    
    return {
        'k_values': k_values,
        'inertias': inertias,
        'silhouette_scores': silhouette_scores,
        'best_k': best_k,
        'inertia_rates': inertia_rates if len(inertia_rates) > 0 else []
    }


def plot_elbow_and_silhouette(results: Dict, output_dir: str = '.'):
    """绘制肘部法则和轮廓系数图"""
    k_values = results['k_values']
    inertias = results['inertias']
    silhouette_scores = results['silhouette_scores']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # 肘部法则图
    ax1.plot(k_values, inertias, 'bo-')
    ax1.set_xlabel('k值')
    ax1.set_ylabel('惯性 (Inertia)')
    ax1.set_title('肘部法则')
    ax1.grid(True)
    ax1.axvline(x=results['best_k'], color='r', linestyle='--', label=f'最优k={results["best_k"]}')
    ax1.legend()
    
    # 轮廓系数图
    ax2.plot(k_values, silhouette_scores, 'ro-')
    ax2.set_xlabel('k值')
    ax2.set_ylabel('轮廓系数 (Silhouette Score)')
    ax2.set_title('轮廓系数')
    ax2.grid(True)
    ax2.axvline(x=results['best_k'], color='r', linestyle='--', label=f'最优k={results["best_k"]}')
    ax2.legend()
    
    plt.tight_layout()
    output_path = '../results/k_selection.png'
    plt.savefig(output_path, dpi=150)
    print(f"\n图表已保存到: {output_path}")
    plt.close()


def get_top_similar_samples(embeddings: np.ndarray, cluster_center: np.ndarray, 
                           cluster_indices: np.ndarray, top_n: int = 10) -> List[int]:
    """找到聚类中心最相似的top_n个样本"""
    # 计算与聚类中心的余弦相似度
    cluster_embeddings = embeddings[cluster_indices]
    similarities = cosine_similarity([cluster_center], cluster_embeddings)[0]
    
    # 获取top_n个最相似的索引（在cluster_indices中的位置）
    top_indices_in_cluster = np.argsort(similarities)[-top_n:][::-1]
    
    # 转换为全局索引
    top_global_indices = cluster_indices[top_indices_in_cluster]
    
    return top_global_indices.tolist()


def generate_cluster_summary(samples: List[Dict], model_name: str = "models/gemini-flash-lite-latest") -> str:
    """使用AI生成聚类摘要"""
    # 准备样本文本
    sample_texts = []
    for i, sample in enumerate(samples[:10], 1):  # 最多10个样本
        output = sample.get('output', '')
        
        # 如果output是JSON字符串，尝试解析并提取关键信息
        if output.startswith('{'):
            try:
                output_json = json.loads(output)
                if isinstance(output_json, dict):
                    intent = output_json.get('intent', {})
                    core_interests = intent.get('core_interests', [])
                    search_queries = intent.get('search_queries', [])
                    # 构建简洁的摘要
                    summary_parts = []
                    if core_interests:
                        summary_parts.append(f"核心兴趣: {', '.join(core_interests[:3])}")
                    if search_queries:
                        summary_parts.append(f"搜索查询: {', '.join(search_queries[:2])}")
                    if summary_parts:
                        sample_text = " | ".join(summary_parts)
                    else:
                        sample_text = str(output)[:300]  # 如果无法解析，使用前300字符
                else:
                    sample_text = str(output)[:300]
            except:
                sample_text = str(output)[:300]
        else:
            sample_text = str(output)[:300]
        
        sample_texts.append(f"样本{i}: {sample_text}")
    
    # 构建prompt - 强调区分度和独特性
    samples_text = "\n".join(sample_texts)
    
    # 提取样本中的独特关键词和模式
    all_keywords = []
    unique_features = []
    for sample_text in sample_texts:
        # 提取特殊关键词
        if '订单' in sample_text or 'Order' in sample_text or 'tracking' in sample_text.lower():
            unique_features.append('订单管理')
        if '账户' in sample_text or 'Account' in sample_text or 'Login' in sample_text:
            unique_features.append('账户相关')
        if '心跳' in sample_text or 'heartbeat' in sample_text.lower():
            unique_features.append('互动功能')
        if '收藏' in sample_text or 'Collectible' in sample_text:
            unique_features.append('收藏价值')
        if '配件' in sample_text or 'Accessories' in sample_text:
            unique_features.append('配件需求')
    
    unique_features_str = "、".join(set(unique_features[:3])) if unique_features else ""
    
    prompt = f"""你正在分析一个用户意图聚类。请生成一个简洁但高度区分性的聚类摘要（2-3句话），要求：

**核心要求：**
1. **突出独特性**：必须强调这个聚类与其他聚类不同的核心特征，避免使用通用描述（如"对逼真婴儿娃娃感兴趣"这种几乎所有聚类都适用的描述）
2. **具体化特征**：使用具体的产品属性、用户行为、使用场景、特殊需求等细节来区分
3. **避免重复**：不要使用其他聚类可能也适用的宽泛描述
4. **强调差异点**：如果样本中有特殊的关键词、行为模式或关注点，必须突出强调

**本聚类观察到的特征：** {unique_features_str if unique_features_str else "请从样本中识别独特特征"}

**样本数据：**
{samples_text}

**输出格式：**
**聚类摘要：**

[你的摘要，必须突出这个聚类的独特性和与其他聚类的区别]

请用中文回答，生成一个能够清晰区分这个聚类与其他聚类的摘要。"""
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"生成摘要时出错: {e}")
        return f"聚类包含 {len(samples)} 个样本"


def main():
    # 配置（相对于scripts目录）
    embeddings_file = "../data/output_embeddings.json"
    csv_file = "../data/ikarao.csv"
    k_range = range(2, 21)  # 测试k从2到20
    top_n_samples = 10
    
    # 加载API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = input("请输入您的Gemini API Key: ").strip()
    genai.configure(api_key=api_key)
    
    # 加载完整output数据（如果可用）
    full_outputs = load_full_outputs(csv_file) if os.path.exists(csv_file) else None
    
    # 加载数据
    embeddings, data = load_embeddings(embeddings_file, full_outputs)
    
    # 寻找最优k
    print("\n" + "="*50)
    k_results = find_optimal_k(embeddings, k_range, sample_size=10000)
    
    # 绘制图表
    plot_elbow_and_silhouette(k_results)
    
    # 使用最优k进行全量数据聚类
    optimal_k = k_results['best_k']
    print(f"\n使用最优k={optimal_k}对全量数据进行聚类...")
    print("="*50)
    
    mbk = MiniBatchKMeans(n_clusters=optimal_k, random_state=42, batch_size=1000, n_init=10)
    labels = mbk.fit_predict(embeddings)
    
    print(f"聚类完成！")
    print(f"聚类分布:")
    unique, counts = np.unique(labels, return_counts=True)
    for cluster_id, count in zip(unique, counts):
        print(f"  聚类 {cluster_id}: {count} 个样本")
    
    # 为每个聚类提取最相似的样本并生成摘要
    print(f"\n为每个聚类提取最相似的{top_n_samples}个样本并生成摘要...")
    print("="*50)
    
    cluster_summaries = []
    
    for cluster_id in range(optimal_k):
        print(f"\n处理聚类 {cluster_id}...")
        
        # 找到该聚类的所有样本
        cluster_indices = np.where(labels == cluster_id)[0]
        cluster_center = mbk.cluster_centers_[cluster_id]
        
        # 归一化聚类中心（用于余弦相似度计算）
        cluster_center_norm = cluster_center / np.linalg.norm(cluster_center) if np.linalg.norm(cluster_center) > 0 else cluster_center
        
        # 获取最相似的样本
        top_indices = get_top_similar_samples(embeddings, cluster_center_norm, cluster_indices, top_n_samples)
        top_samples = [data[idx] for idx in top_indices]
        
        # 生成摘要
        print(f"  生成摘要...")
        summary = generate_cluster_summary(top_samples)
        
        cluster_info = {
            'cluster_id': int(cluster_id),
            'size': int(len(cluster_indices)),
            'top_samples': [
                {
                    'id': sample['id'],
                    'output_preview': sample.get('output', '')[:200]
                }
                for sample in top_samples
            ],
            'summary': summary
        }
        
        cluster_summaries.append(cluster_info)
        
        print(f"  摘要: {summary[:100]}...")
        time.sleep(0.5)  # 避免API限流
    
    # 保存结果
    output_file = "../results/cluster_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'optimal_k': optimal_k,
            'k_selection_results': k_results,
            'cluster_summaries': cluster_summaries,
            'total_samples': len(data)
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_file}")
    
    # 打印摘要
    print("\n" + "="*50)
    print("聚类摘要:")
    print("="*50)
    for cluster_info in cluster_summaries:
        print(f"\n聚类 {cluster_info['cluster_id']} (包含 {cluster_info['size']} 个样本):")
        print(f"  {cluster_info['summary']}")


if __name__ == "__main__":
    main()

