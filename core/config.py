"""
全局配置文件
"""
import os

# ==================== 基础路径配置 ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ==================== 千问API配置 ====================
# 默认兜底置空，运行时从前端会话动态注入环境变量读取密钥
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

# 模型配置
VISION_MODEL = "qwen-vl-max"
TEXT_MODEL = "qwen3.7-plus"

# ==================== RAG配置 ====================
VECTOR_MODEL_NAME = "all-MiniLM-L6-v2"
RAG_TOP_K = 3
RAG_SYMPTOM_TOP_K = 4

# ==================== 数据库配置 ====================
DB_PATH = os.path.join(DATA_DIR, "health_memory.db")

# ==================== 服务配置 ====================
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True

# ==================== CORS配置 ====================
CORS_ORIGINS = ["*"]