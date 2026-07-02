"""
知识库加载模块
负责从JSON文件加载所有知识库数据
"""
import json
import os
from core.config import KNOWLEDGE_DIR

# ==================== 加载知识库文件 ====================
def load_json_file(filename):
    """加载JSON文件"""
    filepath = os.path.join(KNOWLEDGE_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# 穴位基础信息
ACUPOINTS = load_json_file("acupoints.json")

# 配穴方案
PRESCRIPTIONS = load_json_file("prescriptions.json")

# 调理知识
HEALTH_TIPS = load_json_file("health_tips.json")

# 穴位坐标
ACUPOINT_COORDS = load_json_file("acupoint_coords.json")

# ==================== 构建RAG知识文本列表 ====================
def build_knowledge_texts():
    """
    构建用于RAG的知识文本列表
    包含：穴位详情 + 配穴方案 + 调理知识
    """
    texts = []
    
    # 1. 穴位详情
    for name, info in ACUPOINTS.items():
        texts.append(info.get('detail', ''))
    
    # 2. 配穴方案
    for name, info in PRESCRIPTIONS.items():
        texts.append(info.get('detail', ''))
    
    # 3. 调理知识
    for name, info in HEALTH_TIPS.items():
        texts.append(info.get('content', ''))
    
    return texts

KNOWLEDGE_TEXTS = build_knowledge_texts()

# ==================== 工具函数 ====================
def get_acupoint_basic(name):
    """获取穴位基础信息（简化版，用于列表展示）"""
    if name in ACUPOINTS:
        info = ACUPOINTS[name]
        return {
            "meridian": info["meridian"],
            "category": info["category"],
            "body_area": info["body_area"]
        }
    return None

def get_acupoint_detail(name):
    """获取穴位完整详情"""
    if name in ACUPOINTS:
        return ACUPOINTS[name]
    return None

def get_acupoint_coord(name):
    """获取穴位坐标"""
    if name in ACUPOINT_COORDS:
        coord = ACUPOINT_COORDS[name]
        return (coord["x"], coord["y"])
    return None

def get_all_acupoints_list():
    """获取所有穴位列表（用于知识库页面）"""
    result = []
    for name, info in ACUPOINTS.items():
        result.append({
            "name": name,
            "meridian": info["meridian"],
            "category": info.get("category", ""),
            "body_area": info.get("body_area", ""),
            "indications": info.get("indications", [])[:3]
        })
    return result