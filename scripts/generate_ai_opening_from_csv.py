#!/usr/bin/env python3
"""
从CSV文件读取summary列，为每个intent prototype生成AI Opening（TikTok视频脚本）
使用与generate_ai_opening.py相同的prompt和方法
"""
import json
import csv
import os
import sys
from typing import Dict, List
import time

try:
    import google.generativeai as genai
except ImportError:
    print("请先安装google-generativeai: pip install google-generativeai")
    sys.exit(1)

csv.field_size_limit(sys.maxsize)


def load_api_key() -> str:
    """从环境变量获取API key"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("需要设置GEMINI_API_KEY环境变量")
    return api_key


def load_csv_data(csv_file: str) -> List[Dict]:
    """从CSV文件加载数据，提取summary列"""
    print(f"加载CSV数据: {csv_file}")
    data = []
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 提取summary列
            summary = row.get('summary', '').strip()
            if summary:
                data.append({
                    'id': row.get('id', ''),
                    'shop_id': row.get('shop_id', ''),
                    'summary': summary,
                    'status': row.get('status', ''),
                    'cluster_hit': row.get('cluster_hit', '')
                })
    
    print(f"加载了 {len(data)} 条数据")
    return data


def extract_info_from_summary(summary: str) -> Dict:
    """从summary中提取信息（简化版，因为summary是JSON格式）"""
    import json as json_lib
    
    try:
        # 尝试解析JSON格式的summary
        summary_dict = json_lib.loads(summary)
        
        # 提取核心信息
        core_interests = summary_dict.get('core_interests', [])
        product_focus = summary_dict.get('product_focus', {})
        behavior_summary = summary_dict.get('behavior_summary', {})
        match_analysis = summary_dict.get('match_analysis', {})
        
        # 构建文本描述作为cluster summary
        cluster_summary_text = f"""
用户核心兴趣: {', '.join(core_interests) if core_interests else '未指定'}
产品关注点: {product_focus.get('main_appeal', '未指定')}
价格范围: {product_focus.get('price_range', '未指定')}
关键属性: {', '.join(product_focus.get('key_attributes', [])) if product_focus.get('key_attributes') else '未指定'}
用户参与度: {behavior_summary.get('engagement', '未指定')}
浏览路径: {behavior_summary.get('browsing_path', '未指定')}
用户画像: {match_analysis.get('customer_portrait', '未指定')}
使用场景: {match_analysis.get('use_case', '未指定')}
"""
        
        # 提取痛点
        pain_points = []
        if 'concerns' in summary_dict.get('purchase_signals', {}):
            concerns = summary_dict['purchase_signals']['concerns']
            if concerns:
                pain_points.append(f"Concern: {concerns}")
        
        # 从行为摘要中提取
        if 'browsing_path' in behavior_summary:
            if 'uncertainty' in behavior_summary['browsing_path'].lower() or 'confusion' in behavior_summary['browsing_path'].lower():
                pain_points.append("Uncertainty about product choices and features")
        
        if not pain_points:
            pain_points.append("Seeking the perfect product that meets specific needs")
        
        # 提取关键词
        keywords = []
        if core_interests:
            keywords.extend([str(interest).lower() for interest in core_interests[:5]])
        if product_focus.get('key_attributes'):
            keywords.extend([str(attr).lower() for attr in product_focus['key_attributes'][:3]])
        
        if not keywords:
            keywords = ["product", "selection", "quality"]
        
        # 提取动机
        motivation = match_analysis.get('use_case', 'Seeking the perfect product that meets specific needs and preferences')
        
        # 提取情感触发
        emotional_trigger = "Uncertainty about product choices and whether they meet expectations"
        
        # 推断用户画像
        customer_portrait = match_analysis.get('customer_portrait', '')
        if 'collector' in customer_portrait.lower() or 'collectible' in customer_portrait.lower():
            user_profile = "收藏家/Collector - 关注收藏价值、品质、真实性"
            character_role = "collector/connoisseur - 鉴赏者/收藏者形象，关注品质评估、真实性验证"
        elif 'premium' in product_focus.get('price_range', '').lower() or 'high-end' in customer_portrait.lower():
            user_profile = "高端消费者 - 关注品质和体验"
            character_role = "quality-focused consumer - 关注产品品质和体验"
        else:
            user_profile = "对产品感兴趣的消费者"
            character_role = "caring consumer figure - 关注产品选择和体验"
        
        return {
            'cluster_summary_text': cluster_summary_text.strip(),
            'pain_points': pain_points[:3],
            'keywords': keywords[:5],
            'motivation': motivation,
            'emotional_trigger': emotional_trigger,
            'user_profile': user_profile,
            'character_role': character_role
        }
    except (json_lib.JSONDecodeError, Exception) as e:
        # 如果不是JSON格式，直接使用文本
        print(f"警告: 无法解析JSON格式的summary，使用原始文本: {e}")
        return {
            'cluster_summary_text': summary,
            'pain_points': ["Seeking the perfect product that meets specific needs"],
            'keywords': ["product", "selection"],
            'motivation': "Seeking the perfect product that meets specific needs and preferences",
            'emotional_trigger': "Uncertainty about product choices",
            'user_profile': "对产品感兴趣的消费者",
            'character_role': "caring consumer figure"
        }


def generate_ai_opening_from_summary(row: Dict, model_name: str = "models/gemini-flash-lite-latest") -> str:
    """为单个summary生成AI Opening脚本"""
    
    summary = row['summary']
    row_id = row.get('id', 'unknown')
    
    # 从summary中提取信息
    extracted_info = extract_info_from_summary(summary)
    cluster_summary_text = extracted_info['cluster_summary_text']
    clean_summary = cluster_summary_text
    
    # 公司风格（固定为babeside风格）
    company_style = """Babeside品牌风格特征：
- 童趣（Playful & Whimsical）：画面应该充满童真、轻松、天真的氛围，避免过于成熟或严肃的视觉元素
- 温暖（Warm & Cozy）：使用柔和的暖色调（温暖的粉色、奶油色、柔和的黄色、淡橙色），营造舒适、亲切、包裹感强的氛围
- 母爱叙事（Maternal Narrative）：场景应该体现温柔、关爱、呵护的情感，但以童趣的方式呈现
- 视觉元素：可以使用柔和的光线、温馨的环境、舒适的材质（如柔软的毛毯、温暖的灯光、温馨的室内装饰）
- 避免：过于暗沉、严肃、成熟、冷色调、工业化的视觉元素"""
    
    # 构建prompt - 使用与generate_ai_opening.py相同的prompt结构
    prompt = f"""You are an expert TikTok video script writer specializing in emotionally devastating, complete narrative scenes for North American audiences.

CRITICAL FIRST STEP - READ THE CLUSTER SUMMARY CAREFULLY:

Before creating any script, you MUST carefully read and understand the COMPLETE CLUSTER SUMMARY that will be provided below. The cluster summary contains the EXACT characteristics, pain points, behaviors, and interests of this specific user group. Your script MUST be a direct visual translation of EVERY detail mentioned in that cluster summary.

MOST CRITICAL REQUIREMENT - MAXIMUM DIFFERENTIATION:

This video script MUST be COMPLETELY DIFFERENT from all other prototypes. You are creating ONE of MANY unique videos, and each must be instantly recognizable as distinct. Before writing, consider:

1. VISUAL SETTING DIFFERENTIATION:
   - Each prototype MUST have a UNIQUE, DISTINCT setting/environment
   - Avoid generic "cozy nursery" or "warm playroom" - create SPECIFIC, MEMORABLE environments
   - Examples of distinct settings: A collector's organized display corner vs. A mother's preparation space vs. A quality assessment area vs. An accessory matching station
   - The setting itself should tell a story about THIS specific cluster's focus

2. CHARACTER ACTION DIFFERENTIATION:
   - Each prototype MUST have UNIQUE, SPECIFIC opening actions that immediately signal the cluster type
   - Collector: Precise evaluation gestures (measuring, comparing, authenticating)
   - Mother/Interaction: Testing response gestures (checking heartbeat, testing grip, seeking connection)
   - Accessory-focused: Matching/fitting gestures (trying to complete a setup, organizing complementary items)
   - Material-focused: Texture evaluation gestures (feeling, testing softness, comparing feel)
   - Size-focused: Measuring/comparing gestures (comparing scale, checking proportions)
   - The FIRST action in SHOT 1 must be so specific that it immediately identifies this cluster

3. VISUAL METAPHOR DIFFERENTIATION:
   - Each prototype MUST use UNIQUE visual metaphors that represent THIS cluster's specific concern
   - Do NOT reuse the same visual metaphors across prototypes
   - Create NEW, MEMORABLE visual symbols for each cluster

4. EMOTIONAL JOURNEY DIFFERENTIATION:
   - Each prototype MUST have a UNIQUE emotional arc that reflects THIS cluster's specific pain point
   - Collector: Evaluation → Quality concern → FOMO about perfect piece
   - Mother/Interaction: Testing → Expectation gap → Tender acceptance
   - Accessory: Matching → Compatibility concern → Resolution
   - Material: Touching → Authenticity doubt → Quality confirmation
   - The emotional journey must be SPECIFIC to this cluster, not generic

5. SHOT COMPOSITION DIFFERENTIATION:
   - Each prototype MUST have UNIQUE shot compositions and camera movements
   - Vary the opening shot: Close-up on hands vs. Wide establishing vs. Medium character intro
   - Vary camera movements: Static vs. Push-in vs. Lateral drift vs. Rack focus
   - Create DISTINCT visual rhythms for each prototype

Create a COMPLETE, WARM, PLAYFUL scene (MAXIMUM 8 seconds - MUST NOT exceed 8 seconds) that tells a full emotional story - from setup to gentle emotional realization. This must be a COMPLETE SCENE with a clear beginning, middle, and tender emotional moment, all within the 8-second constraint.

IMPORTANT: The scene MUST be based DIRECTLY on the cluster summary provided below. Do NOT create a generic scene. Every visual element, gesture, emotion, and action must reflect the specific characteristics described in the cluster summary. AND it must be COMPLETELY DIFFERENT from all other prototypes.

CRITICAL BABESIDE STYLE REMINDER:
- The scene must feel WARM, PLAYFUL, and CHILDLIKE - like a cozy nursery or warm playroom
- Even disappointment should be expressed GENTLY and TENDERLY - like a caring mother's gentle concern
- Environment should be BRIGHT, WARM, and COZY - NOT dark, moody, or serious
- Think: soft blankets, warm sunlight, cozy rooms, playful textures - NOT elegant salons, serious studies, or moody boudoirs
- Emotions should be TENDER and WARM - NOT devastating, dramatic, or intense

TARGET CLUSTER PROFILE - CRITICAL REFERENCE:

 Prototype ID: {row_id}

 COMPLETE CLUSTER SUMMARY (THIS IS THE PRIMARY SOURCE - YOU MUST FOLLOW THIS EXACTLY):
 {clean_summary}

 ADDITIONAL CLUSTER CHARACTERISTICS:
 - User Profile: {extracted_info['user_profile']}
 - Character Role/Identity: {extracted_info['character_role']}
 - User Pain Points: {', '.join(extracted_info['pain_points'])}
 - Core Keywords: {', '.join(extracted_info['keywords'])}
 - User Motivation: {extracted_info['motivation']}
 - Emotional Trigger: {extracted_info['emotional_trigger']}

CRITICAL REQUIREMENT - CLUSTER SUMMARY ALIGNMENT:

The video script MUST be DIRECTLY and EXPLICITLY based on the COMPLETE CLUSTER SUMMARY above. Every element of the script must reflect the specific characteristics, pain points, and behaviors described in the cluster summary:

1. The visual story MUST directly address the specific concerns mentioned in the cluster summary
2. The character's actions and gestures MUST reflect the specific behaviors and interests described in the cluster summary
3. The emotional journey MUST align with the specific pain points and motivations described in the cluster summary
4. The visual metaphors MUST represent the specific keywords, interests, and attributes from the cluster summary
5. The scene MUST be so specific to THIS cluster summary that it would NOT work for any other cluster

DO NOT create a generic script. The script MUST be a direct visual translation of the cluster summary's specific characteristics.

COMPANY STYLE - BABESIDE BRAND AESTHETIC:

 Brand Style: {company_style}

 CRITICAL: The visual and narrative approach MUST reflect Babeside's brand aesthetic of PLAYFUL WARMTH and CHILDLIKE INNOCENCE. This is NOT a serious, mature, or dramatic brand - it's warm, playful, and childlike.

REQUIREMENTS:

Script must be in English.

Duration: MAXIMUM 8 seconds (CRITICAL: MUST NOT exceed 8 seconds). The video must be between 7-8 seconds, optimally around 7.5-8 seconds. Every shot timing must be carefully calculated to fit within this constraint while still telling a complete story.

Aspect ratio: 9:16 (vertical format).

Character ethnicity: Caucasian only.

CHARACTER DIVERSITY REQUIREMENT:

To create more engaging and relatable content, each prototype should feature DIVERSE character appearances. Vary the following across different prototypes:

- Age: Vary between early 20s, mid-20s, late 20s, early 30s, mid-30s, late 30s, early 40s
- Body type: Vary body types (slim, average, curvy, etc.) - all should feel natural and relatable
- Hair: Vary hair colors and styles (blonde, brunette, redhead, black, wavy, straight, curly, short, long, etc.)
- Physical features: Vary facial features, height, and other natural variations
- Clothing style: Vary clothing (cozy sweaters, soft cardigans, comfortable loungewear, etc.) - all should fit the warm, playful aesthetic

IMPORTANT:
- Each prototype should have a UNIQUE character appearance to increase visual diversity
- All characters should feel authentic, relatable, and appropriate for North American audiences
- Maintain the warm, approachable, maternal aesthetic regardless of appearance
- Avoid stereotypes - focus on authentic, natural diversity

MOST CRITICAL REQUIREMENT - PURE VISUAL NARRATIVE (NO AUDIO INFORMATION):

This video MUST be completely understandable when played on MUTE. Most TikTok users watch videos without sound. Therefore:

- ALL information, emotion, and story MUST be conveyed through VISUAL ELEMENTS ONLY
- The scene must be self-explanatory through: facial expressions, body language, environmental details, visual metaphors, physical actions, and visual storytelling
- Every emotional beat, every story point, every piece of information must be VISUALLY clear
- Use rich visual details: setting, environment, lighting changes, physical gestures, micro-expressions
- The visual narrative must be so strong that removing all audio would not diminish understanding

VISUAL SEQUENCE: Shot-by-shot breakdown with exact timing - MUST have 3-4 SHOTS that tell a complete story within MAXIMUM 8 seconds:

CRITICAL TIMING CONSTRAINT: Total duration MUST NOT exceed 8 seconds. Recommended timing:
- SHOT 1: 2.0-2.5 seconds
- SHOT 2: 2.0-2.5 seconds  
- SHOT 3: 2.0-2.5 seconds
- SHOT 4 (optional): 1.0-1.5 seconds
Total: 7.0-8.0 seconds maximum

CRITICAL: The first 3-4 seconds (SHOTS 1-2) must be COMPLETELY SILENT and visually POWERFUL enough to hook viewers and make them want to unmute.

- SHOT 1: Setup/Context (2.0-2.5s) - SILENT - Establish the scene with IMMEDIATE visual impact
- SHOT 2: Rising tension (2.0-2.5s) - SILENT - The problem becomes clear, anxiety builds through POWERFUL VISUAL CUES
- SHOT 3: Emotional peak/Climax (2.0-2.5s) - COMPLETE SILENCE - The gentle moment of tender realization
- SHOT 4: Aftermath/Reaction (1.0-1.5s) - COMPLETE SILENCE - The lingering emotional impact (OPTIONAL)

NOTE: Each shot must be DISTINCT and contribute to the complete narrative arc. The scene must feel like a complete, self-contained story with a clear emotional journey, all within MAXIMUM 8 seconds. The ENTIRE video (all shots) must be COMPLETELY SILENT - ALL information must be conveyed through visuals only. Every gesture, expression, and visual element must be clear and self-explanatory.

Include detailed specifications for: visual sequence, effects, camera movements, color grading. (NO audio, NO voiceover - complete silence)

Focus on authentic, relatable moments that North American audiences connect with.

Make it MEMORABLE and DISTINCT. The scene should be so specific to this cluster that it couldn't work for any other prototype."""

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"  错误: {e}")
        return f"Error generating script: {str(e)}"


def main():
    # 配置
    csv_file = "../data/intent_prototype_online.csv"
    output_dir = "../results/online_ai_openings"
    model_name = "models/gemini-flash-lite-latest"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载API key
    api_key = load_api_key()
    genai.configure(api_key=api_key)
    
    print("="*70)
    print("AI Opening 生成 (从CSV文件)")
    print("="*70)
    
    # 加载CSV数据
    data = load_csv_data(csv_file)
    
    if not data:
        print("错误: CSV文件中没有找到有效数据")
        return
    
    print(f"\n找到 {len(data)} 条数据，开始生成AI Opening脚本...")
    print("="*70)
    
    results = []
    
    for i, row in enumerate(data, 1):
        row_id = row.get('id', f'row_{i}')
        print(f"\n[{i}/{len(data)}] 处理 ID {row_id}...")
        print(f"  使用summary生成AI Opening脚本...")
        
        try:
            script = generate_ai_opening_from_summary(row, model_name)
            results.append({
                'id': row_id,
                'shop_id': row.get('shop_id', ''),
                'status': row.get('status', ''),
                'cluster_hit': row.get('cluster_hit', ''),
                'summary': row['summary'],
                'ai_opening': script
            })
            print(f"  ✓ 完成")
            time.sleep(1)  # 避免API限流
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            results.append({
                'id': row_id,
                'shop_id': row.get('shop_id', ''),
                'status': row.get('status', ''),
                'cluster_hit': row.get('cluster_hit', ''),
                'summary': row['summary'],
                'ai_opening': f"Error: {str(e)}"
            })
    
    # 保存结果
    output_file = os.path.join(output_dir, "ai_openings.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'generation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': len(results),
                'source_file': csv_file
            },
            'ai_openings': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n保存结果到: {output_file}")
    print(f"\n完成！生成了 {len(results)} 个AI Opening")
    
    # 打印摘要
    print("\n" + "="*70)
    print("AI Opening 摘要:")
    print("="*70)
    for result in results[:5]:  # 只显示前5个
        print(f"\nID {result['id']}:")
        print(f"  脚本预览: {result['ai_opening'][:100]}...")


if __name__ == "__main__":
    main()

