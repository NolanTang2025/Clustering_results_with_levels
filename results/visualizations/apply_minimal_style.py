#!/usr/bin/env python3
"""
将所有可视化HTML页面改为极简主义风格
"""

import re
from pathlib import Path

def apply_minimal_style(html_content):
    """应用极简主义样式到HTML内容"""
    
    # 移除渐变背景
    html_content = re.sub(
        r'background:\s*linear-gradient[^;]+;',
        'background: #ffffff;',
        html_content,
        flags=re.IGNORECASE
    )
    
    # 移除阴影
    html_content = re.sub(
        r'box-shadow:[^;]+;',
        '',
        html_content,
        flags=re.IGNORECASE
    )
    
    # 移除圆角（保留必要的）
    html_content = re.sub(
        r'border-radius:\s*\d+px;',
        '',
        html_content,
        flags=re.IGNORECASE
    )
    
    # 移除transform和动画效果
    html_content = re.sub(
        r'transform:[^;]+;',
        '',
        html_content,
        flags=re.IGNORECASE
    )
    
    # 替换颜色为极简配色
    color_replacements = {
        r'#667eea': '#1a1a1a',
        r'#764ba2': '#1a1a1a',
        r'rgba\(102,\s*126,\s*234[^)]+\)': '#1a1a1a',
        r'rgba\(118,\s*75,\s*162[^)]+\)': '#1a1a1a',
    }
    
    for pattern, replacement in color_replacements.items():
        html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)
    
    # 在head中添加极简样式链接
    if '<link rel="stylesheet" href="minimal_style.css">' not in html_content:
        html_content = re.sub(
            r'(</head>)',
            r'    <link rel="stylesheet" href="minimal_style.css">\n\1',
            html_content
        )
    
    # 替换body背景
    html_content = re.sub(
        r'body\s*\{[^}]*background[^}]*\}',
        'body { background: #ffffff; color: #1a1a1a; }',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    return html_content

def process_html_file(file_path):
    """处理单个HTML文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 应用极简样式
        new_content = apply_minimal_style(content)
        
        # 保存备份
        backup_path = file_path.with_suffix('.html.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 保存新内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 已处理: {file_path.name}")
        return True
    except Exception as e:
        print(f"❌ 处理失败 {file_path.name}: {e}")
        return False

def main():
    """主函数"""
    base_dir = Path('.')
    
    # 获取所有HTML文件（排除index.html和minimal_style.css）
    html_files = [
        f for f in base_dir.glob('*.html')
        if f.name != 'index.html'
    ]
    
    print(f"找到 {len(html_files)} 个HTML文件需要处理\n")
    
    success_count = 0
    for html_file in html_files:
        if process_html_file(html_file):
            success_count += 1
    
    print(f"\n处理完成: {success_count}/{len(html_files)} 个文件")
    print("\n注意: 已创建备份文件 (.backup)")

if __name__ == '__main__':
    main()

