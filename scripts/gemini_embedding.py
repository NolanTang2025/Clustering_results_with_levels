#!/usr/bin/env python3
"""
使用Gemini API为CSV文件中的output列生成embedding
"""
import csv
import sys
import os
import json
from typing import List, Dict
import time
import numpy as np

try:
    import google.generativeai as genai
except ImportError:
    print("请先安装google-generativeai: pip install google-generativeai")
    sys.exit(1)

# 增加CSV字段大小限制
csv.field_size_limit(sys.maxsize)


def load_api_key() -> str:
    """从环境变量或用户输入获取API key"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = input("请输入您的Gemini API Key: ").strip()
        if not api_key:
            raise ValueError("需要提供Gemini API Key")
    return api_key


def normalize_embedding(embedding: List[float]) -> List[float]:
    """对embedding向量进行L2归一化（用于余弦相似度）"""
    vec = np.array(embedding)
    norm = np.linalg.norm(vec)
    if norm > 0:
        return (vec / norm).tolist()
    return embedding


def get_embeddings(texts: List[str], model_name: str = "models/text-embedding-004") -> List[List[float]]:
    """使用Gemini API生成embedding"""
    embeddings = []
    for i, text in enumerate(texts):
        try:
            # text-embedding-004 支持更长的文本，但为了安全起见，限制在8000字符
            if len(text) > 8000:
                text = text[:8000]
            
            result = genai.embed_content(
                model=model_name,
                content=text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            embedding = result['embedding']
            
            # 归一化向量（L2归一化，用于余弦相似度）
            embedding = normalize_embedding(embedding)
            
            embeddings.append(embedding)
            
            # 避免API限流
            if (i + 1) % 10 == 0:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"处理第 {i+1} 条数据时出错: {e}")
            embeddings.append(None)
    
    return embeddings


def process_csv(input_file: str, output_file: str, batch_size: int = 100):
    """处理CSV文件，为output列生成embedding"""
    # 配置API
    api_key = load_api_key()
    genai.configure(api_key=api_key)
    
    print(f"开始处理文件: {input_file}")
    
    # 读取CSV文件
    rows = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('output'):
                rows.append(row)
    
    print(f"找到 {len(rows)} 条包含output的数据")
    
    # 批量处理
    results = []
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        texts = [row['output'] for row in batch]
        
        print(f"处理批次 {i//batch_size + 1}/{(len(rows)-1)//batch_size + 1} ({len(batch)} 条数据)...")
        
        embeddings = get_embeddings(texts)
        
        # 保存结果
        for j, (row, embedding) in enumerate(zip(batch, embeddings)):
            result = {
                'id': row.get('id', ''),
                'output': row['output'][:100] + '...' if len(row['output']) > 100 else row['output'],  # 只保存前100字符作为预览
                'embedding': embedding,
                'embedding_dim': len(embedding) if embedding else 0
            }
            results.append(result)
        
        print(f"已完成 {min(i+batch_size, len(rows))}/{len(rows)} 条数据")
    
    # 保存结果到JSON文件
    print(f"保存结果到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 也保存为CSV格式（embedding作为JSON字符串）
    csv_output = output_file.replace('.json', '_embeddings.csv')
    print(f"同时保存为CSV格式: {csv_output}")
    with open(csv_output, 'w', encoding='utf-8', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=['id', 'output_preview', 'embedding_json', 'embedding_dim'])
            writer.writeheader()
            for result in results:
                writer.writerow({
                    'id': result['id'],
                    'output_preview': result['output'],
                    'embedding_json': json.dumps(result['embedding']) if result['embedding'] else '',
                    'embedding_dim': result['embedding_dim']
                })
    
    print(f"完成！共处理 {len(results)} 条数据")
    print(f"Embedding维度: {results[0]['embedding_dim'] if results else 'N/A'}")


if __name__ == "__main__":
    # 默认路径（相对于scripts目录）
    input_file = "../data/ikarao.csv"
    output_file = "../data/output_embeddings.json"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    process_csv(input_file, output_file)

