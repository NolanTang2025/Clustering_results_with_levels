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
    
    return {
        'pain_points': pain_points[:3],
        'keywords': keywords[:3],
        'motivation': motivation,
        'emotional_trigger': emotional_trigger
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

Create a COMPLETE, WARM, PLAYFUL scene (MAXIMUM 8 seconds - MUST NOT exceed 8 seconds) that tells a full emotional story - from setup to gentle emotional realization. This must be a COMPLETE SCENE with a clear beginning, middle, and tender emotional moment, all within the 8-second constraint.

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
- Voiceover must reference or imply the cluster's specific interests using appropriate language
- The entire scene should be so specific to this cluster that it would be immediately recognizable as representing THIS cluster's story

If the cluster focuses on "material quality/authenticity", the video should show gestures suggesting touching, feeling, or evaluating texture.
If the cluster focuses on "accessories/compatibility", the video should show gestures suggesting matching, fitting, or trying to complete something.
If the cluster focuses on "collectible value", the video should show gestures suggesting evaluating, assessing, or recognizing value.
If the cluster focuses on "interactive features", the video should show gestures suggesting testing, expecting response, or seeking connection.
If the cluster focuses on "size/specifications", the video should show gestures suggesting measuring, comparing, or judging scale.

The visual story must be immediately recognizable as being about THIS specific cluster's concern, not a generic emotional moment.

IMPORTANT: The video should focus on PRODUCT-RELATED pain points and emotions (product selection, product features, product quality concerns, product choice anxiety), NOT process-related issues (order tracking, account management, login issues, shipping status). The emotional hook must be about the PRODUCT itself and the user's relationship with choosing/experiencing the product.

MOST CRITICAL REQUIREMENT - VISUAL-FIRST NARRATIVE:

This video MUST be completely understandable when played on MUTE. Most TikTok users watch videos without sound. Therefore:

- ALL information, emotion, and story MUST be conveyed through VISUAL ELEMENTS ONLY
- The scene must be self-explanatory through: facial expressions, body language, environmental details, visual metaphors, physical actions, and visual storytelling
- Voiceover is OPTIONAL and should only enhance, never carry essential information
- Every emotional beat, every story point, every piece of information must be VISUALLY clear
- Use rich visual details: setting, environment, lighting changes, physical gestures, micro-expressions
- The visual narrative must be so strong that removing all audio would not diminish understanding

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

The scene must NOT show:
- ANY SKU images, product images, or product-related visuals
- ANY specification charts, choice indicators, or option displays
- ANY visual representations of products, choices, or options
- ANY objects, items, or props that could be interpreted as product-related

The emotional confusion, anxiety, and decision-making struggle must be conveyed through:
- Character's expressions, body language, physical reactions
- Rich, detailed environment that reflects and amplifies the emotion
- Dynamic visual elements (lighting, shadows, movement, textures)
- Visual composition that creates impact and interest

TARGET CLUSTER PROFILE:

 Cluster Name: {cluster_name}

 User Pain Points: {', '.join(extracted_info['pain_points'])}

 Core Keywords: {', '.join(extracted_info['keywords'])}

 User Motivation: {extracted_info['motivation']}

 Emotional Trigger: {extracted_info['emotional_trigger']}

CRITICAL: This video MUST be SPECIFICALLY tailored to this cluster's unique characteristics. The visual story, emotional beats, physical actions, and even subtle details MUST reflect this cluster's specific pain points and interests. The video should be so specific to this cluster that it would NOT work for any other cluster.

CLUSTER-SPECIFIC REQUIREMENTS:
- The visual narrative must directly reflect the cluster's primary interests and pain points
- Physical actions and gestures should metaphorically represent the cluster's specific concerns (e.g., if the cluster focuses on "material quality", the character's actions should suggest touching, examining, or evaluating texture/feel)
- The emotional journey must align with the cluster's unique motivation and emotional trigger
- Environmental details, setting, and context should subtly reinforce the cluster's specific focus areas
- The voiceover must reference or imply the cluster's specific concerns (without mentioning products directly)
- Every visual element should contribute to telling THIS specific cluster's story, not a generic emotional scene

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

 3. MATERNAL NARRATIVE (母爱叙事):
    - Emotional tone: Gentle, caring, nurturing - not intense or devastating
    - Character should feel like a caring mother figure, not a dramatic protagonist
    - Even in moments of disappointment, the emotion should be gentle and tender
    - The warmth and care should be evident in every frame

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

Character ethnicity must be Caucasian or Western-looking.

ABSOLUTELY NO SKU IMAGES OR VISUAL REFERENCES: Do not show, mention, or reference any SKU images, product images, specification charts, or any visual representations of products or choices. The scene must be purely about the character, their environment, and their emotional state - NO product-related visuals whatsoever.

NO subtitles/captions needed (visual-only script).

ABSOLUTELY NO PRODUCT: No product shots, no product mentions, no product hints.

Focus on PRODUCT-RELATED PROBLEM and EMOTION only. The emotional hook must be about product selection, product features, product quality concerns, or product choice anxiety - NOT about order tracking, account management, or other process-related issues.

CRITICAL: Must hook viewers in the FIRST 0.5-1.0 seconds with POWERFUL visual impact. This is the moment viewers decide whether to unmute or scroll away. The opening visual must be:
- Immediately emotionally engaging
- Visually striking and memorable
- Self-explanatory without any audio
- Compelling enough to make viewers want to see more and potentially unmute

The first 3-4 seconds are the most critical - they must be completely silent and visually powerful enough to capture and hold attention.

Optimized for North American aesthetic (realistic, authentic, relatable).

Include detailed specifications for: visual sequence, effects, audio, voiceover, camera movements, color grading.

SCRIPT FORMAT:

VISUAL SEQUENCE: Shot-by-shot breakdown with exact timing - MUST have 3-4 SHOTS that tell a complete story within MAXIMUM 8 seconds:

CRITICAL TIMING CONSTRAINT: Total duration MUST NOT exceed 8 seconds. Recommended timing:
- SHOT 1: 2.0-2.5 seconds
- SHOT 2: 2.0-2.5 seconds  
- SHOT 3: 2.0-2.5 seconds
- SHOT 4 (optional): 1.0-1.5 seconds
Total: 7.0-8.0 seconds maximum

CRITICAL: The first 3-4 seconds (SHOTS 1-2) must be COMPLETELY SILENT and visually POWERFUL enough to hook viewers and make them want to unmute.

- SHOT 1: Setup/Context (2.0-2.5s) - SILENT - Establish the scene with IMMEDIATE visual impact that reflects THIS CLUSTER'S specific characteristics:
  * MUST be visually striking from frame 1 (0.0s) with RICH, LAYERED composition
  * Rich environmental context with DETAILED VISUAL ELEMENTS that reflect BABESIDE's playful, warm aesthetic:
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
  * Character's physical position and posture that immediately communicates emotion AND hints at the cluster's specific concern (e.g., hands positioned to suggest examining, touching, or evaluating if the cluster focuses on material/quality)
  * Initial facial expression and body language that hooks attention AND reflects the cluster's unique pain point
  * Visual symbols or metaphors that hint at the emotional state AND the cluster's specific interest (e.g., if cluster focuses on "size", gestures might suggest measuring or comparing; if "interactive features", gestures might suggest testing or expecting response)
  * DYNAMIC environmental details that tell the story:
    - Lighting that creates visual interest (light patterns, shadows, highlights)
    - Environmental elements that add movement or visual interest (curtains, fabric, light shifts)
    - Visual composition that uses the full frame creatively
    - Textural details visible in the environment
  * This shot must be so compelling that viewers are immediately engaged AND must clearly establish this is about THIS specific cluster's concern, not a generic emotional scene
  
- SHOT 2: Rising tension (2.0-2.5s) - SILENT - The problem becomes clear, anxiety builds through POWERFUL VISUAL CUES that are SPECIFIC to this cluster:
  * Physical reactions that metaphorically represent the cluster's specific concern (e.g., if cluster focuses on "material authenticity", the character might gesture as if touching or feeling; if "accessories/compatibility", gestures might suggest trying to match or fit things together)
  * Facial micro-expressions (brow furrowing, eyes darting, lip quivering) that reflect the cluster's specific type of anxiety
  * DRAMATIC environmental changes that create visual impact:
    - Lighting shifts that create visual drama (shadows deepening, light dimming, color temperature changes)
    - Environmental elements reacting (fabric moving, curtains shifting, shadows changing)
    - Focus changes that create visual interest (rack focus, depth of field shifts)
    - Visual composition changes (camera movement, framing shifts)
    - Environmental details that amplify the tension (textures becoming more prominent, shadows creating drama)
  * Body language that communicates internal conflict SPECIFIC to this cluster's dilemma
  * Visual storytelling through action and reaction that clearly relates to the cluster's primary interests
  * RICH visual layers that maintain interest (foreground elements, character, detailed background all working together)
  * By the end of this shot (around 3-4 seconds), viewers should be fully engaged and potentially unmuting, AND should understand this is about THIS specific cluster's concern
  
- SHOT 3: Emotional peak/Climax (2.0-2.5s) - Audio and VOICEOVER BEGIN here (around 4.0-5.0 seconds total) - The gentle moment of tender realization through WARM, PLAYFUL VISUALS that are SPECIFIC to this cluster:
  * Close-up on the gentle emotional moment (soft expression, tender reaction) that reflects the cluster's specific type of gentle disappointment - like a caring mother's gentle concern, NOT dramatic devastation
  * Body language that tells the story GENTLY (soft shoulders dropping slightly, gentle hand gesture, tender physical reaction) AND metaphorically represents the cluster's specific concern in a WARM, PLAYFUL way (e.g., if cluster focuses on "collectible value", the gentle reaction might suggest tender concern about quality; if "interactive features", the gentle reaction might suggest soft disappointment about lack of response)
  * CRITICAL: The emotion should be TENDER and WARM - like a caring mother gently realizing something isn't quite right, NOT dramatic devastation or intense collapse
  * Visual metaphor or symbolic moment that directly relates to the cluster's unique concern
  * GENTLE environmental response that creates WARM VISUAL IMPACT:
    - Lighting changes that are WARM and GENTLE (soft shifts, warm color temperature changes, gentle shadows, warm light patterns shifting) - NEVER cold, harsh, or dramatic
    - Environmental elements reacting GENTLY (soft fabric moving gently, warm curtains shifting softly, warm shadows changing gently, playful textures becoming prominent)
    - Focus and depth changes that create visual interest (rack focus, depth of field shifts, bokeh effects) - but always maintaining warm, playful quality
    - Visual composition that emphasizes the gentle emotional moment with RICH, WARM LAYERS (foreground elements, character, detailed warm background)
    - Environmental details that amplify the tender concern (visible warm textures, playful patterns, warm light creating gentle visual interest, soft shadows creating depth) - NEVER dark, moody, or dramatic
  * Physical action that communicates the emotional devastation SPECIFIC to this cluster's pain point
  * RICH visual composition with multiple layers working together to create maximum impact
  * Audio starts subtly here to enhance the emotional impact
  * VOICEOVER REQUIRED - Must reference or strongly imply the cluster's specific concerns (e.g., if cluster focuses on "material", voiceover might mention "feel" or "texture"; if "accessories", might mention "fit" or "match"; if "collectible", might mention "authenticity" or "value") - 10-20 words that capture BOTH the emotional core AND the cluster-specific concern
  
- SHOT 4: Aftermath/Reaction (1.0-1.5s) - Audio and VOICEOVER continue - The lingering emotional impact through VISUAL RESONANCE that reinforces this cluster's specific story (OPTIONAL - only include if total duration allows, must not exceed 8 seconds total):
  * Final body language and posture that reflects the cluster's specific type of defeat
  * RICH environmental state that creates visual interest and maintains engagement:
    - Environmental details that reflect the emotional aftermath (lighting settling, shadows, textures, patterns)
    - Visual composition that shows the character within a rich, detailed environment (not isolated)
    - Environmental elements that add visual depth and interest (layers, textures, light patterns)
    - Visual layers that maintain engagement (foreground elements, character, detailed background all working together)
    - Environmental atmosphere that reinforces the emotion (visual mood through lighting, shadows, textures)
  * Visual closure that completes the story AND reinforces that this was about THIS specific cluster's concern
  * Audio provides emotional resonance
  * VOICEOVER can continue or conclude here if needed, but must maintain connection to the cluster's specific pain points

NOTE: Each shot must be DISTINCT and contribute to the complete narrative arc. The scene must feel like a complete, self-contained story with a clear emotional journey, all within MAXIMUM 8 seconds. The first 3-4 seconds (SHOTS 1-2) are CRITICAL and must be completely silent, visually powerful, and immediately engaging.

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

CRITICAL AUDIO TIMING REQUIREMENT:

Most TikTok users watch videos on mute initially. They only unmute if the visual hook is strong enough. Therefore:

- FIRST 3-4 SECONDS: COMPLETELY SILENT - NO audio, NO voiceover, NO sound effects. The visual story must be so compelling and self-explanatory that it hooks viewers purely through visuals. This is the critical window where viewers decide whether to unmute or scroll away.

- AFTER 3-4 SECONDS: Audio and VOICEOVER BEGIN to enhance the story, but only after the visual narrative has already established itself. Audio should:
  * Start subtly (low volume ambient sound or gentle music)
  * Build gradually (tension-building sound design)
  * Peak at emotional climax (if appropriate)
  * Provide emotional resonance in closing moments

- VOICEOVER is REQUIRED and should start around 4-5 seconds (after the silent hook period)
- The first 3-4 seconds MUST be visually stunning and emotionally engaging enough to make viewers want to unmute. The visual hook must be immediate and powerful.

AUDIO STRUCTURE (within 8-second constraint):
- 0.0 - 3.0-4.0 seconds: COMPLETE SILENCE - Pure visual storytelling (no audio, no voiceover)
- 3.0-4.0 seconds onwards: Background audio can begin (ambient sound, music, or sound design)
- 4.0-5.0 seconds onwards: VOICEOVER BEGINS (required) - Should appear during emotional peak or aftermath
- Middle section: Tension-building audio continues (within remaining time)
- Climax: Peak emotional audio moment with voiceover (within remaining time)
- Closing: Lingering emotional resonance with voiceover if time allows (MUST end by 8.0 seconds)

CRITICAL: All audio and voiceover must fit within the 8-second total duration. Plan timing carefully.

VOICEOVER: REQUIRED - Must be included in every script, but ONLY appears AFTER the first 3-4 seconds (typically starting around 4-5 seconds). The voiceover MUST be SPECIFIC to this cluster:

- MUST reference or strongly imply the cluster's specific concerns, interests, or pain points (without mentioning products directly)
- Should use language that reflects the cluster's unique focus (e.g., if cluster focuses on "material quality", use words like "feel", "texture", "authenticity"; if "accessories/compatibility", use words like "fit", "match", "complete"; if "collectible value", use words like "real", "authentic", "perfect"; if "interactive features", use words like "response", "connection", "real")
- Be authentic, relatable, and emotionally resonant
- Support the visual story and add emotional depth WHILE reinforcing the cluster's specific concern
- Be 10-20 words total (can be split across shots if needed)
- Match the emotional tone of the scene AND the cluster's specific type of anxiety
- Be delivered in a natural, conversational style (not overly dramatic)
- Appear during the emotional peak or aftermath sections (SHOT 3 or SHOT 4)
- The voiceover should make it clear this is about THIS specific cluster's concern, not a generic emotional moment

The visual story must stand completely alone for the first 3-4 seconds, but voiceover is essential for the complete narrative experience after that point AND must reinforce the cluster-specific connection.

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

CRITICAL FIRST 3-4 SECONDS REQUIREMENT:
- The opening must be IMMEDIATELY visually striking and emotionally engaging
- Every frame in the first 3-4 seconds must be carefully crafted to maximize visual impact
- The visual hook must be so strong that viewers are compelled to continue watching and potentially unmute
- No audio dependency - the story must be 100% clear through visuals alone in this critical window

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

NO product, NO phone, NO technology, NO objects, NO items visible.

ABSOLUTELY NO SKU images, product images, specification charts, or any visual representations of products or choices. The emotional confusion and anxiety must be conveyed purely through the character's expressions, body language, and environment - NOT through any product-related visuals.

ONLY problem and emotion - pure, complete dramatic scene told through VISUALS.

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

CRITICAL RULES - ABSOLUTELY NO PRODUCTS OR OBJECTS:

DO NOT mention product name, features, or any product-related content.

DO NOT show product, phone screens, computers, devices, or technology.

DO NOT show bowls, water containers, or any objects.

DO NOT mention "bowl", "device", "technology", "screen", "computer", "phone" in visual descriptions.

DO NOT show, mention, or reference any SKU images, product images, specification charts, choice indicators, or any visual representations of products or options. The confusion and anxiety must be conveyed purely through the character's emotional expressions, body language, physical reactions, and environmental context - NO product-related visuals whatsoever.

DO NOT include solution hints or product reveals.

ONLY show the problem and emotional reaction - COMPLETE DRAMATIC SCENE.

Focus on facial expressions, body language, and complete emotional journey ONLY.

Focus on authentic, relatable moments that North American audiences connect with.

UNIQUENESS REQUIREMENT:

This scene MUST be completely unique and different from other prototypes. Consider:
- Unique setting or context specific to this cluster's pain points (VISUALLY distinct environment that reflects the cluster's specific focus)
- Unique emotional journey that matches this cluster's specific triggers (VISUALLY distinct emotional arc that is specific to this cluster's concern)
- Unique visual approach that distinguishes this from other prototypes (unique visual style, composition, or visual metaphor that represents this cluster's unique interest)
- Unique narrative structure that tells this cluster's specific story (VISUALLY distinct story progression that reflects this cluster's specific pain point)
- Unique visual symbols, gestures, or physical actions that are specific to this cluster (e.g., if cluster focuses on "material", gestures should suggest touching/feeling; if "accessories", gestures should suggest matching/fitting; if "collectible", gestures should suggest evaluating/assessing value; if "interactive", gestures should suggest testing/expecting response)
- Unique voiceover language that references this cluster's specific concerns (e.g., material-related words, compatibility-related words, collectible-related words, interactive-related words)

Make it MEMORABLE and DISTINCT. The scene should be so specific to this cluster that it couldn't work for any other prototype. A viewer familiar with the clusters should be able to identify which cluster this video represents based on the visual cues, gestures, and voiceover alone.

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
8. Voiceover that references THIS cluster's specific concerns using appropriate language
9. VISUAL IMPACT through rich composition, environmental details, and dynamic visual elements

CRITICAL: Avoid single-person-in-empty-space compositions. Every shot must have RICH visual elements, detailed environments, and multiple layers of visual interest. The scene should feel visually rich and engaging, not sparse or minimal.

Audio and voiceover are enhancements that must reinforce the cluster-specific connection - the visual story must stand completely alone AND clearly represent this specific cluster's story WITH VISUAL RICHNESS AND IMPACT."""
    
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

