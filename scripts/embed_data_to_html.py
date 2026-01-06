#!/usr/bin/env python3
"""
将JSON数据嵌入到HTML文件中，解决CORS问题
"""
import json
import os
import sys
import re

def find_matching_brace(content, start_pos):
    """找到匹配的右大括号位置"""
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_pos, len(content)):
        char = content[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return i
    
    return -1

def embed_data_to_html():
    """将JSON数据嵌入到HTML中"""
    
    # 文件路径
    html_file = "../results/visualization.html"
    cluster_file = "../results/cluster_results.json"
    prototype_file = "../results/intent_prototypes.json"
    non_product_file = "../results/non_product_intent_analysis.json"
    order_tracking_file = "../results/order_tracking_analysis.json"
    output_file = "../results/visualization.html"
    
    # 读取JSON数据
    print("读取JSON数据...")
    with open(cluster_file, 'r', encoding='utf-8') as f:
        cluster_data = json.load(f)
    
    with open(prototype_file, 'r', encoding='utf-8') as f:
        prototype_data = json.load(f)
    
    with open(non_product_file, 'r', encoding='utf-8') as f:
        non_product_data = json.load(f)
    
    try:
        with open(order_tracking_file, 'r', encoding='utf-8') as f:
            order_tracking_data = json.load(f)
    except FileNotFoundError:
        print(f"⚠ 未找到订单追踪分析文件: {order_tracking_file}")
        order_tracking_data = None
    
    # 读取HTML模板
    print("读取HTML模板...")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 将JSON数据转换为JavaScript变量
    cluster_js = json.dumps(cluster_data, ensure_ascii=False, indent=2)
    prototype_js = json.dumps(prototype_data, ensure_ascii=False, indent=2)
    non_product_js = json.dumps(non_product_data, ensure_ascii=False, indent=2)
    if order_tracking_data:
        order_tracking_js = json.dumps(order_tracking_data, ensure_ascii=False, indent=2)
    else:
        order_tracking_js = "{}"
    
    # 替换clusterData
    cluster_match = re.search(r'clusterData\s*=\s*\{', html_content)
    if cluster_match:
        start_pos = cluster_match.start()
        brace_pos = html_content.find('{', start_pos)
        end_pos = find_matching_brace(html_content, brace_pos)
        if end_pos > 0:
            # 找到分号
            semicolon_pos = html_content.find(';', end_pos)
            if semicolon_pos > 0:
                html_content = html_content[:start_pos] + f'clusterData = {cluster_js};' + html_content[semicolon_pos+1:]
                print("✓ 替换了clusterData")
            else:
                print("⚠ 未找到clusterData的结束分号")
        else:
            print("⚠ 未找到clusterData的匹配大括号")
    else:
        print("⚠ 未找到clusterData")
    
    # 替换prototypeData
    prototype_match = re.search(r'prototypeData\s*=\s*\{', html_content)
    if prototype_match:
        start_pos = prototype_match.start()
        brace_pos = html_content.find('{', start_pos)
        end_pos = find_matching_brace(html_content, brace_pos)
        if end_pos > 0:
            # 找到分号
            semicolon_pos = html_content.find(';', end_pos)
            if semicolon_pos > 0:
                html_content = html_content[:start_pos] + f'prototypeData = {prototype_js};' + html_content[semicolon_pos+1:]
                print("✓ 替换了prototypeData")
            else:
                print("⚠ 未找到prototypeData的结束分号")
        else:
            print("⚠ 未找到prototypeData的匹配大括号")
    else:
        print("⚠ 未找到prototypeData")
    
    # 替换nonProductData
    non_product_match = re.search(r'nonProductData\s*=\s*\{', html_content)
    if non_product_match:
        start_pos = non_product_match.start()
        brace_pos = html_content.find('{', start_pos)
        end_pos = find_matching_brace(html_content, brace_pos)
        if end_pos > 0:
            # 找到分号
            semicolon_pos = html_content.find(';', end_pos)
            if semicolon_pos > 0:
                html_content = html_content[:start_pos] + f'nonProductData = {non_product_js};' + html_content[semicolon_pos+1:]
                print("✓ 替换了nonProductData")
            else:
                print("⚠ 未找到nonProductData的结束分号")
        else:
            print("⚠ 未找到nonProductData的匹配大括号")
    else:
        print("⚠ 未找到nonProductData，将在loadData函数中添加")
        # 如果没有找到，在loadData函数中添加
        load_data_match = re.search(r'// 加载非产品相关意图分析数据', html_content)
        if load_data_match:
            # 找到下一个分号或函数结束
            next_semicolon = html_content.find(';', load_data_match.end())
            if next_semicolon > 0:
                # 替换硬编码的数据
                pattern = r'nonProductData = \{[\s\S]*?\};'
                replacement = f'nonProductData = {non_product_js};'
                html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
                print("✓ 替换了nonProductData（在loadData函数中）")
            else:
                print("⚠ 无法定位nonProductData的插入位置")
        else:
            print("⚠ 未找到nonProductData的插入位置")
    
    # 替换orderTrackingData（如果存在）
    if order_tracking_data:
        order_tracking_match = re.search(r'orderTrackingData\s*=\s*\{', html_content)
        if order_tracking_match:
            start_pos = order_tracking_match.start()
            brace_pos = html_content.find('{', start_pos)
            end_pos = find_matching_brace(html_content, brace_pos)
            if end_pos > 0:
                semicolon_pos = html_content.find(';', end_pos)
                if semicolon_pos > 0:
                    html_content = html_content[:start_pos] + f'orderTrackingData = {order_tracking_js};' + html_content[semicolon_pos+1:]
                    print("✓ 替换了orderTrackingData")
                else:
                    print("⚠ 未找到orderTrackingData的结束分号")
            else:
                print("⚠ 未找到orderTrackingData的匹配大括号")
        else:
            # 尝试在nonProductData之后添加orderTrackingData
            non_product_match = re.search(r'nonProductData\s*=\s*\{', html_content)
            if non_product_match:
                # 找到nonProductData的结束位置
                start_pos = non_product_match.start()
                brace_pos = html_content.find('{', start_pos)
                end_pos = find_matching_brace(html_content, brace_pos)
                if end_pos > 0:
                    semicolon_pos = html_content.find(';', end_pos)
                    if semicolon_pos > 0:
                        # 在nonProductData之后添加orderTrackingData
                        insert_pos = semicolon_pos + 1
                        # 检查是否已经有orderTrackingData
                        next_text = html_content[insert_pos:insert_pos+50].strip()
                        if 'orderTrackingData' not in next_text:
                            html_content = (html_content[:insert_pos] + 
                                          f'\n                \n                // 加载订单追踪分析数据\n                orderTrackingData = {order_tracking_js};' + 
                                          html_content[insert_pos:])
                            print("✓ 添加了orderTrackingData（在loadData函数中）")
                        else:
                            # 如果已存在，尝试替换
                            pattern = r'orderTrackingData\s*=\s*\{[^}]*?\};'
                            replacement = f'orderTrackingData = {order_tracking_js};'
                            html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
                            print("✓ 替换了orderTrackingData（在loadData函数中）")
                    else:
                        print("⚠ 未找到nonProductData的结束分号")
                else:
                    print("⚠ 未找到nonProductData的匹配大括号")
            else:
                print("⚠ 未找到nonProductData，无法插入orderTrackingData")
    
    # 保存新的HTML文件
    print(f"保存嵌入数据的HTML到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✓ 完成！数据已嵌入到HTML文件中")
    print(f"✓ 文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")
    
    # 验证
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        proto_count = content.count('"intent_cluster_id"')
        print(f"✓ 验证: HTML中包含 {proto_count} 个prototype")


if __name__ == "__main__":
    embed_data_to_html()
