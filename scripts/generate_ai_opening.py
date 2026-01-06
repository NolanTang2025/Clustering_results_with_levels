#!/usr/bin/env python3
"""
为每个Intent Prototype生成AI Opening（TikTok视频脚本的3秒开头）
"""
import json
import os
import sys
from typing import Dict, List
import time

try:
    import google.generativeai as genai
except ImportError:
    print("请先安装google-generativeai: pip install google-generativeai")
    sys.exit(1)


def load_prototypes(prototypes_file: str) -> Dict:
    """加载prototype数据"""
    with open(prototypes_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_cluster_results(cluster_results_file: str) -> Dict:
    """加载cluster results数据"""
    with open(cluster_results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_cluster_summary_for_prototype(proto: Dict, cluster_results: Dict) -> str:
    """根据prototype获取对应的cluster summary"""
    cluster_id = proto.get('intent_cluster_id', 0)
    
    # 如果是合并的prototype，使用第一个原始cluster的summary
    if proto.get('is_merged', False):
        merged_from = proto.get('merged_from_clusters', [])
        if merged_from:
            # 使用第一个cluster的summary
            first_cluster_id = merged_from[0]
            for cluster in cluster_results.get('cluster_summaries', []):
                if cluster.get('cluster_id') == first_cluster_id:
                    return cluster.get('summary', '')
    
    # 如果不是合并的，直接使用对应的cluster summary
    for cluster in cluster_results.get('cluster_summaries', []):
        if cluster.get('cluster_id') == cluster_id:
            return cluster.get('summary', '')
    
    return ""


def extract_cluster_name(proto: Dict) -> str:
    """提取聚类名称"""
    cluster_id = proto.get('intent_cluster_id', 0)
    if proto.get('is_merged', False):
        merged_from = proto.get('merged_from_clusters', [])
        if len(merged_from) > 1:
            return f"Cluster {cluster_id} (Merged from {len(merged_from)} clusters)"
    return f"Cluster {cluster_id}"


def extract_pain_points(proto: Dict) -> List[str]:
    """从prototype中提取用户痛点"""
    pain_points = []
    
    summary = proto.get('intent_description', {}).get('summary', '').lower()
    behavior_patterns = proto.get('user_intent_characteristics', {}).get('user_behavior_patterns', [])
    
    # 从summary中提取痛点
    if '订单' in summary or 'order' in summary or 'tracking' in summary:
        pain_points.append("Uncertainty about order status and delivery")
    if '账户' in summary or 'account' in summary or 'login' in summary:
        pain_points.append("Difficulty accessing account or managing account information")
    if '查询' in summary or 'search' in summary:
        pain_points.append("Confusion about product options and features")
    if '收藏' in summary or 'collectible' in summary:
        pain_points.append("Worry about missing out on valuable collectible items")
    if '配件' in summary or 'accessories' in summary:
        pain_points.append("Uncertainty about which accessories to choose")
    
    # 从行为模式中提取
    for pattern in behavior_patterns:
        if '订单' in pattern or 'order' in pattern.lower():
            if "Uncertainty about order status" not in str(pain_points):
                pain_points.append("Frustration with order tracking and delivery updates")
        elif '账户' in pattern or 'account' in pattern.lower():
            if "Difficulty accessing account" not in str(pain_points):
                pain_points.append("Account access and management challenges")
    
    # 如果痛点不够，从意图强度推断
    if len(pain_points) < 3:
        intent_strength = proto.get('user_intent_characteristics', {}).get('intent_strength', 'medium')
        if intent_strength == 'high':
            pain_points.append("Urgent need for product information and decision-making")
        elif intent_strength == 'low':
            pain_points.append("Hesitation and uncertainty in purchasing decisions")
    
    # 确保至少有3个痛点
    while len(pain_points) < 3:
        pain_points.append("Confusion and indecision about product choices")
    
    return pain_points[:3]


def extract_keywords(proto: Dict) -> List[str]:
    """提取核心关键词"""
    primary_interests = proto.get('user_intent_characteristics', {}).get('primary_interests', [])
    
    # 转换为英文关键词
    keyword_map = {
        '订单': 'order tracking',
        '账户': 'account management',
        '登录': 'login access',
        '追踪': 'tracking',
        '收藏': 'collectible',
        '配件': 'accessories',
        '硅胶': 'silicone',
        '逼真': 'realistic',
        '重生': 'reborn',
        '心跳': 'heartbeat',
        '呼吸': 'breathing',
        '互动': 'interactive',
        '尺寸': 'size',
        '材质': 'material',
        '性别': 'gender'
    }
    
    keywords = []
    for interest in primary_interests[:5]:
        if interest in keyword_map:
            keywords.append(keyword_map[interest])
        else:
            # 直接使用英文或翻译
            keywords.append(interest.lower())
    
    # 确保至少有3个关键词
    while len(keywords) < 3:
        keywords.append("realistic baby doll")
    
    return keywords[:3]


def extract_motivation(proto: Dict) -> str:
    """提取用户动机"""
    summary = proto.get('intent_description', {}).get('summary', '')
    target_audience = proto.get('marketing_insights', {}).get('target_audience', [])
    
    # 从summary中推断动机
    if '收藏' in summary or 'collectible' in summary.lower():
        return "Desire to build a valuable collection of high-quality items"
    elif '订单' in summary or 'order' in summary.lower() or 'tracking' in summary.lower():
        return "Need for transparency and control over purchase and delivery status"
    elif '账户' in summary or 'account' in summary.lower():
        return "Need for easy access and management of account information"
    elif '互动' in summary or 'interactive' in summary.lower():
        return "Desire for engaging and interactive experiences"
    else:
        return "Seeking the perfect product that meets specific needs and preferences"


def extract_emotional_trigger(proto: Dict) -> str:
    """提取情感触发点"""
    summary = proto.get('intent_description', {}).get('summary', '').lower()
    behavior_patterns = proto.get('user_intent_characteristics', {}).get('user_behavior_patterns', [])
    
    # 根据内容推断情感触发
    if '订单' in summary or 'order' in summary or 'tracking' in summary:
        return "frustration"
    elif '账户' in summary or 'account' in summary or 'login' in summary:
        return "anxiety"
    elif '收藏' in summary or 'collectible' in summary:
        return "fear of missing out (FOMO)"
    elif '查询' in summary or 'search' in summary or 'confusion' in summary:
        return "confusion"
    else:
        return "uncertainty"


def extract_info_from_cluster_summary(cluster_summary: str, proto: Dict) -> Dict:
    """从cluster summary和prototype中提取所需信息，聚焦产品相关痛点而非流程性问题"""
    clean_summary = cluster_summary.replace('**聚类摘要：**', '').replace('**', '').strip()
    summary_lower = clean_summary.lower()
    
    # 提取痛点 - 聚焦产品相关，避免流程性问题（订单追踪、账户管理等）
    pain_points = []
    
    # 产品选择相关痛点
    if '收藏' in clean_summary or 'collectible' in summary_lower:
        pain_points.append("Worry about missing out on the perfect collectible item")
    if '尺寸' in clean_summary or 'size' in summary_lower:
        pain_points.append("Difficulty choosing the right size or specifications for the perfect product")
    if '配件' in clean_summary or 'accessories' in summary_lower:
        pain_points.append("Uncertainty about which accessories will best complement the product")
    if '查询' in clean_summary or 'search' in summary_lower or 'confusion' in summary_lower:
        pain_points.append("Confusion about product options, features, and which one is right")
    if '互动' in clean_summary or 'interactive' in summary_lower:
        pain_points.append("Uncertainty about interactive features and whether they meet expectations")
    if '材质' in clean_summary or 'material' in summary_lower or '硅胶' in clean_summary or 'silicone' in summary_lower:
        pain_points.append("Concern about material quality and authenticity")
    if '逼真' in clean_summary or 'realistic' in summary_lower or '写实' in clean_summary:
        pain_points.append("Worry about whether the product will be realistic enough")
    if '细节' in clean_summary or 'detail' in summary_lower or '特征' in clean_summary or 'feature' in summary_lower:
        pain_points.append("Anxiety about missing important product details or features")
    
    # 如果痛点不够，从prototype补充（聚焦产品相关）
    if len(pain_points) < 3:
        primary_interests = proto.get('user_intent_characteristics', {}).get('primary_interests', [])
        if '硅胶' in str(primary_interests) or 'silicone' in str(primary_interests).lower():
            if not any('material' in pp.lower() or 'quality' in pp.lower() for pp in pain_points):
                pain_points.append("Concern about material quality and durability")
        if '逼真' in str(primary_interests) or 'realistic' in str(primary_interests).lower():
            if not any('realistic' in pp.lower() for pp in pain_points):
                pain_points.append("Worry about whether the product will meet realistic expectations")
        if '收藏' in str(primary_interests) or 'collectible' in str(primary_interests).lower():
            if not any('collectible' in pp.lower() or 'perfect' in pp.lower() for pp in pain_points):
                pain_points.append("Fear of missing out on the perfect collectible item")
    
    while len(pain_points) < 3:
        pain_points.append("Confusion and indecision about product choices")
    
    # 提取关键词
    keywords = []
    primary_interests = proto.get('user_intent_characteristics', {}).get('primary_interests', [])
    keyword_map = {
        '订单': 'order tracking', '账户': 'account management', '登录': 'login access',
        '追踪': 'tracking', '收藏': 'collectible', '配件': 'accessories',
        '硅胶': 'silicone', '逼真': 'realistic', '重生': 'reborn',
        '心跳': 'heartbeat', '呼吸': 'breathing', '互动': 'interactive',
        '尺寸': 'size', '材质': 'material', '性别': 'gender'
    }
    for interest in primary_interests[:5]:
        if interest in keyword_map:
            keywords.append(keyword_map[interest])
        else:
            keywords.append(interest.lower())
    while len(keywords) < 3:
        keywords.append("realistic baby doll")
    
    # 提取动机 - 聚焦产品相关动机
    if '收藏' in clean_summary or 'collectible' in summary_lower:
        motivation = "Desire to find and collect the perfect high-quality product"
    elif '互动' in clean_summary or 'interactive' in summary_lower:
        motivation = "Seeking a product with engaging and interactive features that meet expectations"
    elif '逼真' in clean_summary or 'realistic' in summary_lower or '写实' in clean_summary:
        motivation = "Searching for a product with exceptional realism and authentic details"
    elif '尺寸' in clean_summary or 'size' in summary_lower or '细节' in clean_summary:
        motivation = "Finding the perfect product with the right specifications and details"
    else:
        motivation = "Seeking the perfect product that meets specific needs and preferences"
    
    # 提取情感触发 - 聚焦产品选择相关的情感
    if '收藏' in clean_summary or 'collectible' in summary_lower:
        emotional_trigger = "fear of missing out (FOMO) on the perfect product"
    elif '查询' in clean_summary or 'search' in summary_lower or 'confusion' in summary_lower:
        emotional_trigger = "confusion and indecision about product choices"
    elif '尺寸' in clean_summary or 'size' in summary_lower or '细节' in clean_summary:
        emotional_trigger = "anxiety about choosing the wrong specifications"
    elif '逼真' in clean_summary or 'realistic' in summary_lower:
        emotional_trigger = "worry about whether the product will meet realistic expectations"
    else:
        emotional_trigger = "uncertainty about product choices"
    
    # 提取用户特征 - 用于决定人物形象和情感表达方式
    target_audience = proto.get('marketing_insights', {}).get('target_audience', [])
    user_behavior_patterns = proto.get('user_intent_characteristics', {}).get('user_behavior_patterns', [])
    
    # 根据用户特征推断用户画像
    user_profile = "对逼真婴儿娃娃感兴趣的消费者"  # 默认
    character_role = "caring mother figure"  # 默认
    
    if target_audience:
        if '收藏家' in str(target_audience) or 'collector' in str(target_audience).lower():
            user_profile = "收藏家/Collector - 关注收藏价值、品质、真实性、投资属性"
            character_role = "collector/connoisseur - 鉴赏者/收藏者，关注品质评估、真实性验证、投资价值，不是母亲形象"
        elif '对逼真婴儿娃娃感兴趣的消费者' in str(target_audience):
            user_profile = "对逼真婴儿娃娃感兴趣的消费者"
            character_role = "caring mother figure - 母亲形象，关注互动、体验、情感连接"
    
    if user_behavior_patterns:
        if '收藏价值导向' in str(user_behavior_patterns):
            user_profile = "收藏家/Collector - 关注收藏价值、品质、真实性"
            character_role = "collector/connoisseur - 鉴赏者/收藏者形象，关注品质评估、真实性验证"
        elif '互动功能探索行为' in str(user_behavior_patterns):
            user_profile = "互动功能探索者 - 关注互动功能和体验"
            character_role = "caring mother figure - 母亲形象，关注互动、体验、情感连接"
    
    # 根据摘要进一步确认
    if '收藏' in clean_summary and ('收藏价值' in clean_summary or '艺术品' in clean_summary or '投资' in clean_summary):
        user_profile = "收藏家/Collector - 关注收藏价值、品质、真实性、投资属性"
        character_role = "collector/connoisseur - 鉴赏者/收藏者形象，关注品质评估、真实性验证、投资价值"
    elif '母性模拟' in clean_summary or '玩耍' in clean_summary:
        user_profile = "对逼真婴儿娃娃感兴趣的消费者 - 关注互动和体验"
        character_role = "caring mother figure - 母亲形象，关注互动、体验、情感连接"
    
    return {
        'pain_points': pain_points[:3],
        'keywords': keywords[:3],
        'motivation': motivation,
        'emotional_trigger': emotional_trigger,
        'user_profile': user_profile,
        'character_role': character_role
    }


def generate_ai_opening(proto: Dict, cluster_summary: str, model_name: str = "models/gemini-flash-lite-latest") -> str:
    """为单个prototype生成AI Opening脚本"""
    
    # 提取cluster名称
    cluster_name = extract_cluster_name(proto)
    
    # 清理cluster summary（移除markdown格式）
    clean_summary = cluster_summary.replace('**聚类摘要：**', '').replace('**', '').strip()
    
    # 从cluster summary和prototype中提取信息
    extracted_info = extract_info_from_cluster_summary(cluster_summary, proto)
    
    # 公司风格（固定为babeside风格）
    company_style = """Babeside品牌风格特征：
- 童趣（Playful & Whimsical）：画面应该充满童真、轻松、天真的氛围，避免过于成熟或严肃的视觉元素
- 温暖（Warm & Cozy）：使用柔和的暖色调（温暖的粉色、奶油色、柔和的黄色、淡橙色），营造舒适、亲切、包裹感强的氛围
- 母爱叙事（Maternal Narrative）：场景应该体现温柔、关爱、呵护的情感，但以童趣的方式呈现
- 视觉元素：可以使用柔和的光线、温馨的环境、舒适的材质（如柔软的毛毯、温暖的灯光、温馨的室内装饰）
- 避免：过于暗沉、严肃、成熟、冷色调、工业化的视觉元素"""
    
    # 构建prompt - 使用完整的TARGET CLUSTER PROFILE格式，强调完整场景和区分度
    prompt = f"""You are an expert TikTok video script writer specializing in emotionally devastating, complete narrative scenes for North American audiences.

CRITICAL FIRST STEP - READ THE CLUSTER SUMMARY CAREFULLY:

Before creating any script, you MUST carefully read and understand the COMPLETE CLUSTER SUMMARY that will be provided below. The cluster summary contains the EXACT characteristics, pain points, behaviors, and interests of this specific user group. Your script MUST be a direct visual translation of EVERY detail mentioned in that cluster summary.

MOST CRITICAL REQUIREMENT - MAXIMUM DIFFERENTIATION:

This video script MUST be COMPLETELY DIFFERENT from all other prototypes. You are creating ONE of SEVEN unique videos, and each must be instantly recognizable as distinct. Before writing, consider:

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

MOST CRITICAL REQUIREMENT - CLUSTER SPECIFICITY:

Each prototype MUST have a UNIQUE, DISTINCT scene that is completely different from other prototypes. The scene must be SPECIFIC to this cluster's unique pain points, emotional triggers, primary interests, and core keywords. NO generic scenarios - make it UNIQUE and MEMORABLE.

The video MUST clearly reflect this cluster's specific characteristics:
- Visual elements (gestures, actions, setting) must metaphorically represent the cluster's specific concerns
- Emotional journey must align with the cluster's unique pain points
- Visual elements must clearly convey the cluster's specific interests and concerns
- The entire scene should be so specific to this cluster that it would be immediately recognizable as representing THIS cluster's story

IMPORTANT: All gestures and visual metaphors must relate to REALISTIC SILICONE BABY DOLLS:

If the cluster focuses on "material quality/authenticity", the video should show gestures suggesting:
- Touching, feeling, or evaluating the silicone texture (as if checking if it feels like real baby skin)
- Gently caressing or testing the softness and realism of the material
- Comparing the feel against expectations of realistic baby skin texture

If the cluster focuses on "accessories/compatibility", the video should show gestures suggesting:
- Matching, fitting, or trying to complete a baby care setup (clothing, accessories for the doll)
- Testing if accessories fit or work together with the doll
- Organizing or arranging items that complement the baby doll

If the cluster focuses on "collectible value", the video should show gestures suggesting:
- Evaluating, assessing, or recognizing the quality and authenticity of a collectible baby doll
- Carefully examining details that indicate value and authenticity
- Comparing different options for the perfect collectible piece

If the cluster focuses on "interactive features", the video should show gestures suggesting:
- Testing, expecting response, or seeking connection (as if checking if the doll responds realistically)
- Gently interacting with something that should feel alive or responsive
- Seeking realistic interaction or feedback from the doll

If the cluster focuses on "size/specifications", the video should show gestures suggesting:
- Measuring, comparing, or judging scale (as if checking if the doll size matches expectations)
- Evaluating proportions and size accuracy
- Comparing size against expectations for a realistic baby doll

The visual story must be immediately recognizable as being about THIS specific cluster's concern, not a generic emotional moment.

IMPORTANT: The video should focus on REALISTIC SILICONE BABY DOLL product-related pain points and emotions:
- Product selection anxiety (choosing the right realistic silicone baby doll)
- Material quality concerns (silicone texture, realism, authenticity)
- Product features evaluation (size, specifications, accessories, interactive features)
- Product choice anxiety (FOMO on perfect collectible, worry about authenticity)
- Emotional connection concerns (realism, interactive response, tactile quality)

NOT process-related issues (order tracking, account management, login issues, shipping status). 

The emotional hook must be about REALISTIC SILICONE BABY DOLLS and the user's relationship with choosing/evaluating/experiencing these products. All visual metaphors, gestures, and expressions should relate to concerns about realistic silicone baby dolls.

MOST CRITICAL REQUIREMENT - PURE VISUAL NARRATIVE (NO AUDIO INFORMATION):

This video MUST be completely understandable when played on MUTE. The video will have NO VOICEOVER and NO AUDIO that conveys information. ALL information must be conveyed through visuals ONLY. Therefore:

- ALL information, emotion, and story MUST be conveyed through VISUAL ELEMENTS ONLY
- The scene must be self-explanatory through: facial expressions, body language, environmental details, visual metaphors, physical actions, and visual storytelling
- NO VOICEOVER - the video is completely silent in terms of information delivery
- NO AUDIO that conveys information - only optional ambient sound (no meaning, no narrative purpose)
- Every emotional beat, every story point, every piece of information must be VISUALLY clear and self-explanatory
- Use rich visual details: setting, environment, lighting changes, physical gestures, micro-expressions
- The visual narrative must be 100% complete and understandable without any audio or voiceover whatsoever
- Every gesture, expression, and visual element must clearly communicate the cluster's specific concern

VISUAL RICHNESS REQUIREMENT - CREATE VISUAL IMPACT:

The scene must be visually RICH and DYNAMIC, not just a single person in an empty space. Include:

- RICH ENVIRONMENTAL DETAILS:
  * Detailed, textured backgrounds (fabric textures, wall details, furniture, decorative elements)
  * Multiple layers of visual interest (foreground, midground, background elements)
  * Environmental elements that tell the story (curtains moving, light patterns, shadows, reflections)
  * Textural details (soft fabrics, surfaces, materials in the environment)
  * Depth and dimension in the scene composition

- DYNAMIC VISUAL ELEMENTS:
  * Environmental movement (curtains, fabric, light shifts, shadows moving)
  * Visual transitions and changes (lighting shifts, focus changes, color transitions)
  * Layered composition with multiple visual elements
  * Visual depth through foreground/background relationships
  * Environmental reactions to emotion (e.g., light dimming, shadows deepening, fabric moving)

- VISUAL CONTRAST AND IMPACT:
  * Strong visual contrast between different shots
  * Dramatic lighting changes that create visual interest
  * Composition that uses the full frame, not just centered character
  * Visual elements that create depth and dimension
  * Environmental details that amplify the emotional story

- SCENE COMPOSITION:
  * Use the full 9:16 frame creatively
  * Include environmental elements that add visual interest
  * Create visual layers (character in foreground, rich environment in background)
  * Use depth of field to create visual separation and interest
  * Include visual elements that move or change (not static backgrounds)

The scene CAN and SHOULD show:
- The realistic silicone baby doll (仿真硅胶baby娃娃) - shown naturally in warm, caring context
- Accessories related to the doll (clothing, blankets, etc.) - shown naturally in the scene
- The doll being held, examined, evaluated, or interacted with - in a way that matches the user profile:
  * If collector/connoisseur: EXAMINING, ASSESSING, EVALUATING - like a valuable collectible
  * If mother figure: CARING, INTERACTING, CONNECTING - like caring for a baby

The scene should AVOID:
- SKU images, specification charts, or technical product details
- Product packaging, labels, barcodes, or marketing materials
- Harsh product photography or commercial advertisement style
- Phone screens, computers, devices, or technology

The emotional confusion, anxiety, and decision-making struggle must be conveyed through:
- Character's expressions, body language, physical reactions
- Rich, detailed environment that reflects and amplifies the emotion
- Dynamic visual elements (lighting, shadows, movement, textures)
- Visual composition that creates impact and interest

TARGET CLUSTER PROFILE - CRITICAL REFERENCE:

 Cluster Name: {cluster_name}

 COMPLETE CLUSTER SUMMARY (THIS IS THE PRIMARY SOURCE - YOU MUST FOLLOW THIS EXACTLY):
 {clean_summary}

 ADDITIONAL CLUSTER CHARACTERISTICS:
 - User Profile: {extracted_info['user_profile']}
 - Character Role/Identity: {extracted_info['character_role']}
 - User Pain Points: {', '.join(extracted_info['pain_points'])}
 - Core Keywords: {', '.join(extracted_info['keywords'])}
 - Primary Interests: {', '.join(proto.get('user_intent_characteristics', {}).get('primary_interests', [])[:5])}
 - User Behavior Patterns: {', '.join(proto.get('user_intent_characteristics', {}).get('user_behavior_patterns', []))}
 - Target Audience: {', '.join(proto.get('marketing_insights', {}).get('target_audience', []))}
 - Product Categories: {', '.join(proto.get('product_alignment', {}).get('product_categories', []))}
 - Key Product Attributes: {', '.join(proto.get('product_alignment', {}).get('key_product_attributes', []))}
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

CRITICAL CHARACTER DESIGN REQUIREMENT:

The character in the video MUST match the user profile and character role of THIS specific cluster:

- If the user profile is "收藏家/Collector" and character role is "collector/connoisseur":
  * The character should be a COLLECTOR/CONNOISSEUR, NOT a mother figure
  * Focus should be on EVALUATION, ASSESSMENT, AUTHENTICATION - like examining a valuable collectible
  * Emotions should reflect CONNOISSEURSHIP: careful examination, quality assessment, authenticity verification, investment consideration
  * Gestures should suggest EVALUATION and ASSESSMENT: careful inspection, comparison, quality checking, not maternal care
  * The interaction with the doll should feel like examining a COLLECTIBLE ART PIECE, not caring for a baby
  * Environment can still be warm and cozy, but the character's role and emotions must be COLLECTOR-focused, not MOTHER-focused

- If the user profile suggests "caring mother figure" or focuses on "interaction/experience":
  * The character can be a CARING MOTHER FIGURE
  * Focus should be on CARE, INTERACTION, EMOTIONAL CONNECTION
  * Emotions should reflect MATERNAL CONCERN: tender care, gentle interaction, emotional connection
  * Gestures should suggest CARE and INTERACTION: holding, cradling, testing interaction, not evaluation

- The character's appearance, emotions, gestures, and interactions MUST align with the user profile
- Do NOT default to a "mother" image if the user profile is clearly a "collector/connoisseur"
- The emotional connection must be appropriate for the user type (collector = quality/authenticity concern, mother = care/interaction concern)

CRITICAL: This video MUST be SPECIFICALLY tailored to this cluster's unique characteristics as described in the COMPLETE CLUSTER SUMMARY above. The visual story, emotional beats, physical actions, and even subtle details MUST DIRECTLY reflect the specific descriptions, pain points, behaviors, and interests mentioned in the cluster summary. The video should be so specific to this cluster summary that it would NOT work for any other cluster.

MANDATORY CLUSTER SUMMARY ALIGNMENT CHECKLIST:

Before generating the script, verify that EVERY element aligns with the cluster summary:

✓ Does the visual story directly address the specific concerns mentioned in the cluster summary?
✓ Do the character's actions reflect the specific behaviors described in the cluster summary?
✓ Does the emotional journey match the specific pain points from the cluster summary?
✓ Do the visual metaphors represent the specific keywords and interests from the cluster summary?
✓ Is the character role appropriate for the target audience mentioned in the cluster summary?
✓ Are the gestures and interactions specific to the primary interests listed in the cluster summary?
✓ Does the scene reflect the user behavior patterns described in the cluster summary?

If ANY element does not directly align with the cluster summary, the script is WRONG and must be regenerated.

CLUSTER-SPECIFIC REQUIREMENTS (Based on Cluster Summary):
- The visual narrative must directly reflect the cluster summary's specific descriptions of user needs and interests
- Physical actions and gestures must represent the EXACT concerns mentioned in the cluster summary (e.g., if cluster summary says "收藏价值", show evaluation/assessment gestures; if it says "配件", show matching/fitting gestures; if it says "互动功能", show testing/response gestures)
- The emotional journey must align with the EXACT pain points and motivations described in the cluster summary
- Environmental details, setting, and context must reinforce the SPECIFIC focus areas mentioned in the cluster summary
- Visual elements must clearly convey the EXACT concerns described in the cluster summary (without showing products directly)
- Every visual element must contribute to telling THIS specific cluster's story as described in the cluster summary, not a generic emotional scene

PRODUCT INFORMATION - BABESIDE PRODUCTS:

 Babeside specializes in realistic silicone baby dolls (仿真硅胶baby娃娃). These are highly realistic, lifelike silicone baby dolls designed for collectors, hobbyists, and those seeking emotional connection.

 Key Product Characteristics:
 - Material: Silicone (硅胶) - soft, realistic texture that mimics real baby skin
 - Appearance: Highly realistic, lifelike baby features
 - Purpose: Collecting, emotional connection, realistic baby care simulation
 - Quality Focus: Authenticity, realism, material quality, collectible value
 - Common Concerns: Material authenticity, texture/feel realism, size/specifications, accessories compatibility, interactive features

 CRITICAL: The video script must reflect pain points and emotions related to REALISTIC SILICONE BABY DOLLS. The gestures, expressions, and visual metaphors should relate to:
 - Evaluating the realism and authenticity of silicone material
 - Concerns about texture, feel, and tactile quality
 - Worries about size, specifications, and accessories compatibility
 - Anxiety about interactive features and realistic responses
 - FOMO about collectible value and perfect quality

 The visual story should metaphorically represent concerns about choosing, evaluating, or experiencing realistic silicone baby dolls - NOT generic products or abstract items.

COMPANY STYLE - BABESIDE BRAND AESTHETIC:

 Brand Style: {company_style}

 CRITICAL: The visual and narrative approach MUST reflect Babeside's brand aesthetic of PLAYFUL WARMTH and CHILDLIKE INNOCENCE. This is NOT a serious, mature, or dramatic brand - it's warm, playful, and childlike.

 VISUAL REQUIREMENTS FOR BABESIDE STYLE:

 1. PLAYFUL & WHIMSICAL (童趣):
    - Environment should feel light, airy, and playful - not heavy or serious
    - Use soft, rounded visual elements (avoid harsh angles or industrial looks)
    - Include playful details: soft textures, gentle patterns, whimsical lighting
    - Character expressions should be gentle and innocent, not overly dramatic or intense
    - Avoid dark, moody, or overly sophisticated settings
    - Think: cozy nursery, warm playroom, soft bedroom - not elegant salon or serious study

 2. WARM & COZY (温暖):
    - Color palette: Warm pinks, soft creams, gentle yellows, light oranges, warm beiges
    - Lighting: Soft, diffused, golden hour quality - never harsh or cold
    - Environment: Comfortable, inviting spaces with soft fabrics, plush textures, warm materials
    - Atmosphere: Enveloping, nurturing, safe - like being wrapped in a warm blanket
    - Avoid: Cool tones (blues, greys), harsh lighting, cold or sterile environments

 3. CHARACTER ROLE & EMOTIONAL TONE (根据用户特征调整):
    - The character's role MUST match the user profile and character role:
      * If user profile is "收藏家/Collector": Character is a COLLECTOR/CONNOISSEUR - focus on evaluation, assessment, authentication, NOT maternal care
      * If user profile suggests "mother figure": Character can be a caring mother figure - focus on care, interaction, emotional connection
    - Emotional tone: Gentle, caring, nurturing - but the TYPE of care depends on user profile:
      * For collectors: Care about QUALITY, AUTHENTICITY, INVESTMENT VALUE (like examining a valuable collectible)
      * For mothers: Care about INTERACTION, EMOTIONAL CONNECTION, EXPERIENCE (like caring for a baby)
    - Even in moments of disappointment, the emotion should be gentle and tender, but APPROPRIATE to the user type
    - The warmth should be evident, but the CHARACTER ROLE must match the user profile
    - Do NOT default to a "mother" image if the user profile is clearly a "collector/connoisseur"

 4. SPECIFIC VISUAL ELEMENTS:
    - Soft, plush fabrics (velvet, fleece, soft cotton)
    - Warm, diffused lighting (like golden hour or soft window light)
    - Cozy environments (comfortable rooms, soft furniture, warm textures)
    - Gentle, rounded shapes (avoid sharp, angular, industrial elements)
    - Playful details (soft patterns, gentle textures, warm decorative elements)
    - Character should feel approachable and warm, not distant or dramatic

 5. AVOID:
    - Dark, moody atmospheres
    - Harsh, dramatic lighting
    - Serious, mature, or sophisticated settings
    - Cool color tones (blues, greys, cold whites)
    - Industrial or minimalist aesthetics
    - Overly dramatic or intense emotional expressions
    - Heavy, serious, or formal environments

 The entire scene should feel like a warm, playful, childlike moment - even when dealing with disappointment, it should be gentle and tender, not devastating or dramatic.

REQUIREMENTS:

Script must be in English.

Duration: MAXIMUM 8 seconds (CRITICAL: MUST NOT exceed 8 seconds). The video must be between 7-8 seconds, optimally around 7.5-8 seconds. Every shot timing must be carefully calculated to fit within this constraint while still telling a complete story.

Aspect ratio: 9:16 (vertical format).

CHARACTER REQUIREMENT (North American Caucasian Focus):

To create engaging and relatable content for North American audiences, each prototype should feature Caucasian/White characters with varied age appearances. Vary the following across different prototypes:

- Age: Vary between early 20s, mid-20s, late 20s, early 30s, mid-30s, late 30s, early 40s - different age groups to create visual variety
- Ethnicity: Caucasian/White only - appropriate for North American target audience preferences
- Body type: Vary body types (slim, average, curvy, etc.) - all should feel natural and relatable
- Hair: Vary hair colors and styles (blonde, brunette, redhead, auburn, wavy, straight, curly, short, long, etc.) - keep it natural and warm
- Physical features: Vary facial features, height, and other natural variations within Caucasian features
- Clothing style: Vary clothing (cozy sweaters, soft cardigans, comfortable loungewear, etc.) - all should fit the warm, playful, childlike aesthetic

CRITICAL: MAINTAIN CHILDLIKE INNOCENCE (童真):
- Character expressions should always be gentle, innocent, and childlike - even for older characters
- Avoid overly mature, sophisticated, or serious appearances
- Facial features should be soft and approachable, not sharp or angular
- The overall character appearance should feel warm, playful, and innocent
- Maintain the childlike, playful aesthetic regardless of age - older characters should still have a gentle, innocent quality

IMPORTANT: 
- Each prototype should have a UNIQUE character appearance (vary age, hair, features) to increase visual diversity
- All characters must be Caucasian/White to match North American audience preferences
- All characters should feel authentic, relatable, and appropriate for North American audiences
- Maintain the warm, approachable, childlike aesthetic regardless of appearance
- The character should feel childlike and innocent, even if they are in their 30s or 40s

PRODUCT VISUALIZATION GUIDELINES:

The video CAN and SHOULD include the realistic silicone baby doll (仿真硅胶baby娃娃) as part of the visual story, but it must be presented in a warm, playful, childlike way that fits Babeside's aesthetic:

- The baby doll can appear in the scene naturally (being held, examined, evaluated)
- The doll should be shown in a warm, caring, maternal context (cozy nursery, playroom, comfortable setting)
- The doll should feel like a natural part of the character's emotional journey
- The interaction with the doll should be gentle, tender, and warm - like a mother caring for a baby
- The doll should be shown in soft focus or as part of the warm environment, not as a product advertisement

AVOID:
- SKU images, specification charts, or technical product details
- Product packaging, labels, or marketing materials
- Harsh product lighting or commercial photography style
- Product shots that feel like advertisements

The doll should feel like a natural, emotional element in the story, not a product showcase.

NO subtitles/captions needed (visual-only script).

Focus on PRODUCT-RELATED PROBLEM and EMOTION. The emotional hook must be about realistic silicone baby doll selection, features, quality concerns, or choice anxiety - NOT about order tracking, account management, or other process-related issues.

CRITICAL: Must hook viewers in the FIRST 0.5-1.0 seconds with POWERFUL visual impact. This is the moment viewers decide whether to unmute or scroll away. The opening visual must be:
- Immediately emotionally engaging
- Visually striking and memorable
- Self-explanatory without any audio
- Compelling enough to make viewers want to see more and potentially unmute

The first 3-4 seconds are the most critical - they must be completely silent and visually powerful enough to capture and hold attention.

Optimized for North American aesthetic (realistic, authentic, relatable).

Include detailed specifications for: visual sequence, effects, camera movements, color grading. (NO audio, NO voiceover - complete silence)

SCRIPT FORMAT:

VISUAL SEQUENCE: Shot-by-shot breakdown with exact timing - MUST have 3-4 SHOTS that tell a complete story within MAXIMUM 8 seconds:

CRITICAL TIMING CONSTRAINT: Total duration MUST NOT exceed 8 seconds. Recommended timing:
- SHOT 1: 2.0-2.5 seconds
- SHOT 2: 2.0-2.5 seconds  
- SHOT 3: 2.0-2.5 seconds
- SHOT 4 (optional): 1.0-1.5 seconds
Total: 7.0-8.0 seconds maximum

CRITICAL: The first 3-4 seconds (SHOTS 1-2) must be COMPLETELY SILENT and visually POWERFUL enough to hook viewers and make them want to unmute.

- SHOT 1: Setup/Context (2.0-2.5s) - SILENT - Establish the scene with IMMEDIATE visual impact that reflects THIS CLUSTER'S specific characteristics FROM THE CLUSTER SUMMARY:
  * MUST be visually striking from frame 1 (0.0s) with RICH, LAYERED composition
  * CRITICAL DIFFERENTIATION: This opening shot MUST be COMPLETELY UNIQUE from all other prototypes:
    - Vary the opening shot type: Some start with extreme close-up on specific gesture, some with wide establishing of unique environment, some with medium character intro in distinct setting
    - Vary the opening action: Each prototype must start with a DIFFERENT, SPECIFIC action that immediately signals the cluster type (e.g., collector = precise evaluation gesture, mother = interaction test, accessory = matching gesture, material = texture test, size = measuring gesture)
    - Vary the environment: Each prototype must have a DISTINCT, MEMORABLE setting (not generic "cozy nursery" - be SPECIFIC: "collector's organized display corner" vs. "mother's preparation space" vs. "quality assessment area")
  * Character should be Caucasian/White with DRAMATICALLY VARIED appearance across prototypes:
    - Age: Vary significantly (early 20s vs. mid-30s vs. late 30s) - make each character feel like a different person
    - Hair: Vary dramatically (blonde vs. brunette vs. auburn vs. redhead, wavy vs. straight vs. curly, short vs. long)
    - Body type: Vary (slim vs. average vs. curvy)
    - Clothing: Vary style (cardigan vs. sweater vs. loungewear) - all warm but distinct
    - Character role: Vary the character's role/purpose (Collector vs. Mother vs. Quality Assessor vs. Accessory Coordinator)
  * CRITICAL: The character's initial action/gesture MUST be UNIQUE and SPECIFIC to this cluster:
    - This action must be so distinct that it immediately identifies this cluster type
    - Do NOT use generic "holding doll" or "looking at doll"
    - Be SPECIFIC: "precise texture evaluation with index finger" vs. "testing heartbeat response with hand on chest" vs. "matching accessory compatibility by comparing items"
    - The action must directly reflect the PRIMARY INTERESTS or BEHAVIOR PATTERNS mentioned in the cluster summary
  * Rich environmental context with DETAILED VISUAL ELEMENTS that reflect BABESIDE's playful, warm aesthetic AND the specific context mentioned in the cluster summary:
    - Warm, cozy environments - SPECIFIC EXAMPLES:
      * GOOD: Cozy nursery with soft blankets, warm sunlight streaming through soft curtains, plush carpet, soft toys visible, warm wooden furniture with rounded edges
      * GOOD: Warm playroom with soft cushions, gentle lighting, playful patterns, comfortable seating
      * GOOD: Soft bedroom with warm bed linens, gentle morning light, cozy textures, playful decorative elements
      * BAD: Elegant salon, serious study, moody boudoir, dimly lit room, ornate furniture, antique pieces, sophisticated settings
    - Soft, playful textures (plush fabrics, soft blankets, warm materials, gentle patterns) - think soft fleece, warm cotton, gentle textures
    - Multiple layers (foreground elements, midground character, detailed background) - all with warm, playful, childlike quality
    - Environmental details that are warm and playful:
      * GOOD: Soft curtains with gentle patterns, cozy furniture with rounded edges, warm decorative elements (soft toys, gentle patterns), gentle light patterns (warm sunlight, soft window light)
      * BAD: Heavy velvet curtains, ornate furniture, antique lace, moody lighting, dramatic shadows
    - Visual depth and dimension (not flat, single-plane composition) - but always maintaining warm, playful atmosphere
    - Setting that subtly suggests the cluster's focus BUT in a warm, playful, childlike way:
      * If cluster focuses on "collectible value": Cozy, warm space with soft display elements (like a warm nursery with gentle organization), NOT an elegant gallery
      * If "accessories": Warm, playful preparation space (like a cozy room with soft organization), NOT a serious workspace
    - AVOID: Dark, moody, serious, mature, or sophisticated environments - everything should feel warm, playful, and childlike
  * Character's physical position and posture that immediately communicates emotion AND directly reflects the SPECIFIC concern mentioned in the cluster summary (e.g., if cluster summary says "收藏价值", show evaluation posture; if it says "配件", show matching posture; if it says "材质", show touching/evaluating posture)
  * Initial facial expression and body language that hooks attention AND directly reflects the EXACT pain point described in the cluster summary
  * Visual symbols or metaphors that hint at the emotional state AND directly represent the SPECIFIC keywords/interests from the cluster summary (e.g., if cluster summary mentions "尺寸", gestures should suggest measuring/comparing; if it mentions "互动功能", gestures should suggest testing/expecting response; if it mentions "收藏", gestures should suggest evaluating/assessing value)
  * DYNAMIC environmental details that tell the story:
    - Lighting that creates visual interest (light patterns, shadows, highlights)
    - Environmental elements that add movement or visual interest (curtains, fabric, light shifts)
    - Visual composition that uses the full frame creatively
    - Textural details visible in the environment
  * This shot must be so compelling that viewers are immediately engaged AND must clearly establish this is about THIS specific cluster's concern, not a generic emotional scene
  
- SHOT 2: Rising tension (2.0-2.5s) - SILENT - The problem becomes clear, anxiety builds through POWERFUL VISUAL CUES that are SPECIFIC to this cluster:
  * CRITICAL DIFFERENTIATION: This shot's tension-building approach MUST be UNIQUE to this cluster:
    - Each cluster must have a DIFFERENT way of showing anxiety/concern
    - Collector: Quality doubt through careful re-examination, comparison gestures, authenticity checking
    - Mother/Interaction: Expectation gap through testing response, seeking connection that doesn't come, interaction disappointment
    - Accessory: Compatibility concern through trying to fit items, matching attempts that don't work, organization struggle
    - Material: Authenticity doubt through texture testing, feel comparison, quality uncertainty
    - Size: Proportion concern through measuring, scale comparison, size uncertainty
  * Physical reactions that metaphorically represent the cluster's SPECIFIC concern - must be UNIQUE to this cluster type:
    - Do NOT reuse the same gestures across prototypes
    - Each cluster must have DISTINCT gesture vocabulary
    - Be SPECIFIC: "precise re-examination of texture" vs. "testing heartbeat response" vs. "trying to match accessory compatibility"
  * Facial micro-expressions (brow furrowing, eyes darting, lip quivering) that reflect the cluster's SPECIFIC type of anxiety - must be UNIQUE:
    - Collector: Focused, analytical concern (brow furrowed in evaluation, eyes scanning for quality markers)
    - Mother/Interaction: Hopeful then disappointed (eyes searching for response, then gentle disappointment)
    - Accessory: Matching uncertainty (eyes darting between items, trying to find compatibility)
    - Material: Authenticity doubt (careful examination expression, testing feel)
    - Size: Proportion concern (measuring expression, comparing scale)
  * DRAMATIC environmental changes that create visual impact:
    - Lighting shifts that create visual drama (shadows deepening, light dimming, color temperature changes)
    - Environmental elements reacting (fabric moving, curtains shifting, shadows changing)
    - Focus changes that create visual interest (rack focus, depth of field shifts)
    - Visual composition changes (camera movement, framing shifts)
    - Environmental details that amplify the tension (textures becoming more prominent, shadows creating drama)
  * Body language that communicates internal conflict SPECIFIC to this cluster's dilemma
  * Visual storytelling through action and reaction that clearly relates to the cluster's primary interests
  * RICH visual layers that maintain interest (foreground elements, character, detailed background all working together)
  * By the end of this shot (around 3-4 seconds), viewers should be fully engaged and should understand this is about THIS specific cluster's concern - all through visuals alone
  
- SHOT 3: Emotional peak/Climax (2.0-2.5s) - COMPLETE SILENCE - The gentle moment of tender realization through WARM, PLAYFUL VISUALS that are SPECIFIC to this cluster (ALL information through visuals ONLY):
  * Close-up on the gentle emotional moment (soft expression, tender reaction) that reflects the cluster's specific type of gentle disappointment - like a caring mother's gentle concern, NOT dramatic devastation
  * Body language that tells the story GENTLY and CLEARLY (soft shoulders dropping slightly, gentle hand gesture, tender physical reaction) AND metaphorically represents the cluster's specific concern in a WARM, PLAYFUL way - MUST be visually clear what the concern is (e.g., if cluster focuses on "collectible value", the gentle reaction might suggest tender concern about quality through specific gestures; if "interactive features", the gentle reaction might suggest soft disappointment about lack of response through specific gestures)
  * CRITICAL: The emotion should be TENDER and WARM - like a caring mother gently realizing something isn't quite right, NOT dramatic devastation or intense collapse
  * Visual metaphor or symbolic moment that directly relates to the cluster's unique concern - MUST be visually self-explanatory
  * GENTLE environmental response that creates WARM VISUAL IMPACT and communicates information:
    - Lighting changes that are WARM and GENTLE (soft shifts, warm color temperature changes, gentle shadows, warm light patterns shifting) - NEVER cold, harsh, or dramatic
    - Environmental elements reacting GENTLY (soft fabric moving gently, warm curtains shifting softly, warm shadows changing gently, playful textures becoming prominent)
    - Focus and depth changes that create visual interest (rack focus, depth of field shifts, bokeh effects) - but always maintaining warm, playful quality
    - Visual composition that emphasizes the gentle emotional moment with RICH, WARM LAYERS (foreground elements, character, detailed warm background)
    - Environmental details that amplify the tender concern (visible warm textures, playful patterns, warm light creating gentle visual interest, soft shadows creating depth) - NEVER dark, moody, or dramatic
  * Physical action that communicates the emotional moment SPECIFIC to this cluster's pain point - MUST be visually clear what the concern is
  * RICH visual composition with multiple layers working together to create maximum impact
  * CRITICAL: NO AUDIO, NO VOICEOVER - ALL information must be conveyed through visuals only. Every gesture, expression, and visual element must be clear and self-explanatory.
  
- SHOT 4: Aftermath/Reaction (1.0-1.5s) - COMPLETE SILENCE - The lingering emotional impact through VISUAL RESONANCE that reinforces this cluster's specific story (OPTIONAL - only include if total duration allows, must not exceed 8 seconds total):
  * Final body language and posture that reflects the cluster's specific type of gentle concern - MUST be visually clear what the concern is
  * RICH environmental state that creates visual interest and maintains engagement:
    - Environmental details that reflect the emotional aftermath (lighting settling, shadows, textures, patterns)
    - Visual composition that shows the character within a rich, detailed environment (not isolated)
    - Environmental elements that add visual depth and interest (layers, textures, light patterns)
    - Visual layers that maintain engagement (foreground elements, character, detailed background all working together)
    - Environmental atmosphere that reinforces the emotion (visual mood through lighting, shadows, textures)
  * Visual closure that completes the story AND reinforces that this was about THIS specific cluster's concern - MUST be visually clear and complete
  * CRITICAL: NO AUDIO, NO VOICEOVER - ALL information must be conveyed through visuals only

NOTE: Each shot must be DISTINCT and contribute to the complete narrative arc. The scene must feel like a complete, self-contained story with a clear emotional journey, all within MAXIMUM 8 seconds. The ENTIRE video (all shots) must be COMPLETELY SILENT - ALL information must be conveyed through visuals only. Every gesture, expression, and visual element must be clear and self-explanatory.

CRITICAL TIMING REMINDER: 
- Total duration MUST NOT exceed 8.0 seconds
- Calculate exact timing for each shot to ensure total is 7.0-8.0 seconds
- If including SHOT 4, adjust other shots' durations accordingly to stay within 8 seconds
- Every second counts - be precise with timing

VISUAL EFFECTS: Use cinematic effects strategically to enhance the emotional impact and convey information:
- Subtle slow motion at key emotional moments (60fps) to emphasize emotional beats
- Natural lighting with dramatic shifts to match emotional beats (lighting tells the story)
- Strategic use of focus pulls and depth of field to guide attention and convey emotion
- Color temperature shifts to reflect emotional state (visual emotional language)
- Visual transitions that communicate story progression

CRITICAL: COMPLETE SILENCE - PURE VISUAL STORYTELLING:

This video MUST be COMPLETELY SILENT with NO audio, NO voiceover, and NO sound effects that convey information. The ENTIRE story must be told through visuals alone.

- ENTIRE DURATION (0.0-8.0 seconds): COMPLETE SILENCE - NO audio, NO voiceover, NO sound effects that convey information at any point
- Optional: Very subtle ambient sound (no meaning, no narrative purpose) may be included, but it must NOT convey any information
- The visual story must be so compelling and self-explanatory that it tells a complete narrative through visuals only
- Every emotion, every story beat, every piece of information MUST be conveyed through:
  * Facial expressions and micro-expressions
  * Body language and gestures
  * Environmental details and context
  * Visual metaphors and symbols
  * Lighting and color changes
  * Physical actions and reactions
  * Composition and camera movement

- The visual narrative must be 100% complete and understandable without any audio or voiceover whatsoever
- Viewers must be able to understand the entire story, the cluster's specific concern, and the emotional journey purely through visual elements
- Use rich, detailed visuals to compensate for the absence of audio - every visual element must contribute to the story
- Every gesture, expression, and visual element must be clear and self-explanatory

CAMERA MOVEMENTS: Dynamic, cinematic techniques that serve the story:
- Opening: Establishing movement (push-in, pull-back, or static)
- Middle: Movement that builds tension (slow push-in, subtle pan)
- Climax: Movement that emphasizes the emotional peak (tight push-in, focus pull, or dramatic static)
- Closing: Movement that lingers on the emotion (slow pull-back or static hold)

COLOR GRADING: Apply Babeside's playful, warm brand style with gentle emotional progression:
- Opening: Warm, soft pink tones with cream and gentle yellow accents - playful, cozy, childlike warmth
- Middle: Slight shift to slightly deeper warm tones (warmer pinks, soft oranges) - but always maintaining the playful, warm quality, never becoming dark or cold
- Climax: Soft, warm color moment - may deepen slightly but always stays in warm, playful tones (warm pinks, soft roses, gentle peaches) - NEVER cool, dark, or harsh
- Closing: Return to base warm pink/cream tones with gentle emotional residue - maintaining the childlike, warm, playful quality throughout

CRITICAL: All color grading must maintain Babeside's playful, warm, childlike aesthetic. Avoid:
- Cool tones (blues, greys, cold whites)
- Dark, moody color grading
- Harsh color contrasts
- Serious or dramatic color shifts
- Industrial or sophisticated color palettes

The color should always feel warm, soft, playful, and childlike - like a warm, cozy nursery or playroom.

STYLE GUIDELINES (NORTH AMERICAN AESTHETIC):

Complete scene structure with clear narrative arc (beginning, middle, climax) - all told through VISUALS.

CRITICAL VISUAL-ONLY REQUIREMENT (ENTIRE DURATION):
- The ENTIRE video must be IMMEDIATELY visually striking and emotionally engaging
- Every frame must be carefully crafted to maximize visual impact and story clarity
- The visual hook must be so strong that viewers are compelled to continue watching
- NO audio dependency - the story must be 100% clear through visuals alone for the ENTIRE duration
- Every visual element must be purposeful and contribute to telling the complete story

Realistic, authentic approach (not over-exaggerated, but emotionally powerful) - emotions must be readable through visual cues, especially in the first 3-4 seconds.

Natural lighting and settings that reflect Babeside's playful, warm aesthetic:
- Warm, cozy home environments (comfortable rooms, soft spaces, warm interiors)
- Soft, diffused lighting (golden hour quality, warm window light, gentle ambient light)
- Playful, childlike settings (cozy nursery, warm playroom, soft bedroom) - NOT elegant, serious, or sophisticated spaces
- Environment must tell part of the story with warm, playful, childlike quality
- Avoid: Dark, moody, serious, mature, or sophisticated settings

RICH, LAYERED VISUAL COMPOSITION - CRITICAL FOR VISUAL IMPACT:
- Every shot must have MULTIPLE LAYERS of visual interest (not just a character in empty space)
- Include detailed environmental elements (textured fabrics, furniture, decorative elements, architectural details)
- Use the full 9:16 frame creatively with foreground, midground, and background elements
- Create visual depth through composition, lighting, and focus
- Include environmental elements that add movement or visual interest (curtains, fabric, light patterns, shadows)
- Show textural details in the environment (fabric textures, surface textures, material details)
- Environmental elements should react to or amplify the emotion (lighting shifts, shadows, fabric movement)
- Visual composition should be DYNAMIC, not static - use camera movement, focus changes, and environmental changes to create interest

Genuine emotional reactions that build to a gentle, warm climax - every emotion must be VISUALLY clear but maintain Babeside's playful, warm, childlike quality:
  * Facial expressions (gentle micro-expressions, soft eye movements, tender mouth changes) - emotions should be tender and warm, not intense or dramatic
  * Body language (soft posture, gentle gestures, tender physical reactions) - movements should be gentle and warm, not dramatic or intense
  * RICH environmental details (soft lighting changes, warm space, cozy atmosphere, playful textures, warm layers, childlike visual elements)
  * Physical actions (gentle hands, soft movement, tender stillness) - all actions should feel warm and playful
  * Environmental reactions (soft fabric moving gently, warm shadows shifting softly, warm light changing gently, playful textures becoming prominent)
  * CRITICAL: Even in moments of disappointment, the emotion should be gentle, tender, and warm - like a caring mother's gentle concern, not dramatic devastation. The warmth and playfulness should always be present.

Strategic use of slow motion at key emotional moments (60fps) to emphasize visual storytelling.

Focus on facial expressions, body language, and complete emotional journey - ALL information must be visual.

NO screen shake (distracting).

Use cinematic effects strategically (not extreme, but impactful) to enhance visual narrative.

PRODUCT VISUALIZATION:

The realistic silicone baby doll (仿真硅胶baby娃娃) CAN and SHOULD appear in the scene - shown naturally in a warm, caring, maternal context. The doll should be held, examined, or interacted with in a gentle, tender way that fits Babeside's aesthetic.

AVOID:
- SKU images, specification charts, or technical product details
- Product packaging, labels, or marketing materials
- Phone screens, computers, devices, or technology
- Harsh product photography or commercial style

The scene should show the character's emotional journey with the realistic silicone baby doll - their care, evaluation, concern, or gentle disappointment - all in a warm, playful, childlike way.

ONLY the character and their emotional journey - nothing else, but the visual storytelling must be RICH and DETAILED.

VISUAL STORYTELLING REQUIREMENTS:

- Every shot must contain VISUAL INFORMATION that advances the story
- Use environmental details to establish context (room type, time of day, mood)
- Use physical actions to show internal state (hands, posture, movement)
- Use lighting and color to communicate emotion
- Use focus and composition to guide attention
- Use visual metaphors and symbols when appropriate
- Ensure every emotional beat is VISUALLY readable
- The scene must work perfectly when muted

PRODUCT VISUALIZATION RULES:

PRODUCTS THAT CAN BE SHOWN:
- The realistic silicone baby doll (仿真硅胶baby娃娃) CAN and SHOULD appear in the scene
- The doll can be held, examined, evaluated, or interacted with
- The doll should be shown in a warm, caring, maternal context
- Accessories related to the doll (clothing, blankets, etc.) can appear naturally

PRODUCTS/VISUALS TO AVOID:
- SKU images, specification charts, or technical product details
- Product packaging, labels, barcodes, or marketing materials
- Phone screens, computers, devices, or technology
- Harsh product photography or commercial advertisement style
- Product shots that feel like catalog images

STYLE REQUIREMENTS FOR PRODUCT VISUALIZATION:
- The doll should appear naturally in the warm, cozy environment
- The interaction should be gentle, tender, and maternal - like caring for a real baby
- The doll should be in soft focus or naturally integrated into the scene
- Lighting should be warm and diffused, not harsh or commercial
- The doll should feel like an emotional element, not a product showcase

Focus on the character's emotional journey with the realistic silicone baby doll - showing their care, evaluation, concern, or gentle disappointment - all in a warm, playful, childlike way.

Focus on authentic, relatable moments that North American audiences connect with.

MANDATORY DIFFERENTIATION CHECKLIST - VERIFY BEFORE GENERATING:

Before finalizing your script, verify that EVERY element is UNIQUE and DIFFERENT from other prototypes:

✓ SETTING: Is the environment/context completely different from other prototypes? (Not just "cozy nursery" - be SPECIFIC: "collector's organized display corner" vs. "mother's preparation space" vs. "quality assessment area")

✓ OPENING ACTION: Is the FIRST action in SHOT 1 completely unique? (Not generic "holding doll" - be SPECIFIC: "precise texture evaluation" vs. "testing heartbeat response" vs. "matching accessory compatibility")

✓ VISUAL METAPHOR: Are the visual symbols/metaphors completely unique? (Create NEW metaphors, don't reuse: "authenticity seal check" vs. "interaction response test" vs. "accessory harmony match")

✓ EMOTIONAL ARC: Is the emotional journey completely unique? (Not generic "concern → acceptance" - be SPECIFIC: "evaluation → quality doubt → FOMO" vs. "testing → expectation gap → tender acceptance" vs. "matching → compatibility concern → resolution")

✓ SHOT STRUCTURE: Is the shot composition and camera movement completely unique? (Vary opening shots, camera movements, visual rhythms - make each prototype visually distinct in its cinematography)

✓ CHARACTER GESTURES: Are the specific gestures completely unique? (Each cluster must have DISTINCT gesture vocabulary: collector = evaluation gestures, mother = interaction gestures, accessory = matching gestures, material = texture gestures)

✓ VISUAL DETAILS: Are the environmental details completely unique? (Not generic "soft blankets" - be SPECIFIC: "organized collectible display with measurement tools" vs. "preparation space with accessory options" vs. "quality assessment area with comparison samples")

CRITICAL: If ANY element feels similar to another prototype, you MUST change it. Each prototype should be so visually distinct that a viewer could identify which cluster it represents within the FIRST 2 SECONDS, based solely on the visual setting and opening action.

UNIQUENESS REQUIREMENT - ENHANCED:

This scene MUST be completely unique and different from ALL other prototypes. Consider these DIFFERENTIATION DIMENSIONS:

1. CHARACTER APPEARANCE & ROLE:
   - Vary age significantly across prototypes (early 20s vs. mid-30s vs. late 30s)
   - Vary hair color and style dramatically (blonde vs. brunette vs. auburn vs. redhead)
   - Vary body type and clothing style (slim with cardigan vs. average with sweater vs. curvy with loungewear)
   - Vary character ROLE: Collector/Connoisseur vs. Caring Mother vs. Quality Assessor vs. Accessory Coordinator
   - Each character should feel like a DIFFERENT person with a DIFFERENT purpose

2. SETTING & ENVIRONMENT:
   - Create SPECIFIC, MEMORABLE environments that are visually distinct:
     * Collector: Organized display corner with measurement tools, quality assessment setup, comparison samples
     * Mother/Interaction: Preparation space with testing area, interaction tools, response-checking setup
     * Accessory: Matching station with organized accessories, compatibility testing area, completion-focused space
     * Material: Texture evaluation area with comparison samples, authenticity checking setup
     * Size: Measurement space with scale references, proportion comparison area
   - Each environment should tell a story about THIS cluster's specific focus
   - Avoid generic "cozy nursery" - be SPECIFIC and MEMORABLE

3. OPENING ACTION & GESTURE:
   - Each prototype MUST start with a UNIQUE, SPECIFIC action that immediately signals the cluster type:
     * Collector: Precise evaluation gesture (measuring proportions, checking authenticity marks, comparing quality)
     * Mother/Interaction: Testing response gesture (checking heartbeat, testing grip, seeking connection)
     * Accessory: Matching gesture (trying to fit accessory, organizing complementary items, testing compatibility)
     * Material: Texture evaluation gesture (feeling silicone, testing softness, comparing feel)
     * Size: Measuring gesture (comparing scale, checking proportions, evaluating size)
   - The FIRST action must be so specific that it immediately identifies this cluster
   - Do NOT use generic "holding doll" or "looking at doll" - be SPECIFIC

4. VISUAL METAPHOR & SYMBOLS:
   - Create UNIQUE visual metaphors for each cluster:
     * Collector: Quality seals, measurement tools, comparison samples, authenticity markers
     * Mother/Interaction: Response indicators, connection signals, interaction feedback, heartbeat monitors
     * Accessory: Matching systems, compatibility grids, completion checklists, harmony indicators
     * Material: Texture samples, quality comparisons, authenticity tests, feel evaluations
     * Size: Scale references, proportion guides, measurement tools, size comparisons
   - Do NOT reuse the same visual metaphors across prototypes
   - Each metaphor should be SPECIFIC to this cluster's concern

5. EMOTIONAL JOURNEY:
   - Each prototype MUST have a UNIQUE emotional arc:
     * Collector: Careful evaluation → Quality concern → FOMO about perfect collectible piece
     * Mother/Interaction: Hopeful testing → Expectation gap → Tender acceptance of connection
     * Accessory: Eager matching → Compatibility concern → Resolution through finding right fit
     * Material: Curious touching → Authenticity doubt → Quality confirmation through feel
     * Size: Careful measuring → Proportion concern → Acceptance of scale
   - The emotional journey must be SPECIFIC to this cluster's pain point, not generic

6. SHOT COMPOSITION & CINEMATOGRAPHY:
   - Vary opening shots dramatically:
     * Some start with extreme close-up on hands/gesture
     * Some start with wide establishing shot of environment
     * Some start with medium character introduction
     * Some start with specific object/detail focus
   - Vary camera movements:
     * Static hold vs. Slow push-in vs. Lateral drift vs. Rack focus vs. Pull-back
   - Create DISTINCT visual rhythms for each prototype

7. VISUAL DETAILS & PROPS:
   - Each prototype should have UNIQUE visual details and props:
     * Collector: Measurement tools, quality assessment items, comparison samples, authenticity markers
     * Mother/Interaction: Interaction testing tools, response indicators, connection elements
     * Accessory: Multiple accessory options, matching systems, compatibility indicators
     * Material: Texture samples, quality comparisons, feel testing items
     * Size: Scale references, measurement tools, proportion guides
   - These details should be SPECIFIC to this cluster's focus

Make it MEMORABLE and DISTINCT. The scene should be so specific to this cluster that it couldn't work for any other prototype. A viewer familiar with the clusters should be able to identify which cluster this video represents within the FIRST 2 SECONDS, based SOLELY on the visual setting, opening action, and character role - NO audio or voiceover needed.

FINAL REMINDER - VISUAL-FIRST, CLUSTER-SPECIFIC, AND VISUALLY RICH:

Remember: This script will be viewed by users who are likely watching on mute. Every single piece of information, every emotion, every story beat must be conveyed through VISUAL ELEMENTS. The script must be a complete, self-contained visual story that requires NO audio to understand. BUT it must also be SPECIFIC to this cluster AND VISUALLY RICH. Prioritize:
1. Visual storytelling above all else
2. RICH, LAYERED visual composition with multiple elements (not just a character in empty space):
   - Detailed environmental backgrounds with texture and depth
   - Multiple visual layers (foreground, midground, background)
   - Environmental elements that add visual interest (curtains, fabric, furniture, decorative elements)
   - Dynamic visual elements (lighting shifts, shadows, movement, textures)
   - Full frame utilization with creative composition
3. Rich visual details and environmental context that reflect THIS cluster's specific focus
4. Clear, readable body language and facial expressions that communicate THIS cluster's specific type of anxiety
5. Visual metaphors and symbols that represent THIS cluster's unique concerns
6. Environmental storytelling through lighting, space, atmosphere, textures, and visual layers that reinforces THIS cluster's context
7. Physical actions that communicate internal states AND metaphorically represent THIS cluster's specific pain point (e.g., examining, touching, matching, testing, evaluating)
8. Visual elements that clearly convey THIS cluster's specific concerns through gestures, expressions, and actions
9. VISUAL IMPACT through rich composition, environmental details, and dynamic visual elements

CRITICAL: Avoid single-person-in-empty-space compositions. Every shot must have RICH visual elements, detailed environments, and multiple layers of visual interest. The scene should feel visually rich and engaging, not sparse or minimal.

The visual story must stand completely alone (NO audio, NO voiceover) AND clearly represent this specific cluster's story WITH VISUAL RICHNESS AND IMPACT. Every piece of information must be conveyed through visuals only."""
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"生成AI Opening时出错: {e}")
        return f"Error generating opening for {cluster_name}: {str(e)}"


def main():
    # 文件路径
    prototypes_file = "../results/intent_prototypes.json"
    cluster_results_file = "../results/cluster_results.json"
    output_file = "../results/ai_openings.json"
    
    # 加载API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = input("请输入您的Gemini API Key: ").strip()
    genai.configure(api_key=api_key)
    
    print("="*70)
    print("AI Opening 生成")
    print("="*70)
    
    print("\n加载prototype数据...")
    data = load_prototypes(prototypes_file)
    prototypes = data.get('intent_prototypes', [])
    
    print("加载cluster results数据...")
    cluster_results = load_cluster_results(cluster_results_file)
    
    print(f"找到 {len(prototypes)} 个prototype")
    
    ai_openings = []
    
    for i, proto in enumerate(prototypes, 1):
        cluster_id = proto.get('intent_cluster_id', 0)
        cluster_name = extract_cluster_name(proto)
        
        print(f"\n[{i}/{len(prototypes)}] 处理 {cluster_name}...")
        
        # 获取对应的cluster summary
        cluster_summary = get_cluster_summary_for_prototype(proto, cluster_results)
        if not cluster_summary:
            print(f"  ⚠ 警告: 未找到对应的cluster summary，跳过")
            continue
        
        print(f"  使用cluster summary生成AI Opening脚本...")
        
        # 生成AI Opening
        opening_script = generate_ai_opening(proto, cluster_summary)
        
        ai_openings.append({
            'prototype_id': cluster_id,
            'cluster_name': cluster_name,
            'is_merged': proto.get('is_merged', False),
            'merged_from_clusters': proto.get('merged_from_clusters', []),
            'cluster_summary': cluster_summary,
            'ai_opening': opening_script
        })
        
        print(f"  ✓ 完成")
        time.sleep(0.5)  # 避免API限流
    
    # 保存结果
    output_data = {
        'metadata': {
            'generation_date': __import__('datetime').datetime.now().isoformat(),
            'total_prototypes': len(ai_openings),
            'source_file': prototypes_file
        },
        'ai_openings': ai_openings
    }
    
    print(f"\n保存结果到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成！生成了 {len(ai_openings)} 个AI Opening")
    
    # 打印摘要
    print("\n" + "="*70)
    print("AI Opening 摘要:")
    print("="*70)
    for opening in ai_openings:
        print(f"\n{opening['cluster_name']}:")
        summary_preview = opening.get('cluster_summary', '')[:100].replace('\n', ' ')
        print(f"  Cluster Summary: {summary_preview}...")
        script_preview = opening['ai_opening'][:150].replace('\n', ' ')
        print(f"  脚本预览: {script_preview}...")


if __name__ == "__main__":
    main()

