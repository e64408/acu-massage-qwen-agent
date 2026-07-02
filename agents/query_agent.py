"""
穴位查询Agent
负责查询穴位的详细信息
"""
import dashscope
from dashscope import Generation
from typing import Dict
from core.config import TEXT_MODEL, DASHSCOPE_BASE_URL
from core.rag import rag_search
from knowledge import get_acupoint_basic

# 仅保留接口地址，不再读取环境变量
dashscope.base_http_api_url = DASHSCOPE_BASE_URL

# 新增入参 user_api_key
def query_point_agent(point_name: str, user_api_key: str) -> Dict:
    """
    穴位查询Agent
    
    Args:
        point_name: 穴位名称
        user_api_key: 当前会话用户的千问API密钥
    
    Returns:
        穴位详细信息
    """
    if not user_api_key:
        return {
            "success": False,
            "msg": "未配置通义千问API密钥，请刷新页面重新输入密钥"
        }
    # 函数内强制绑定本次用户密钥
    dashscope.api_key = user_api_key

    rag_context = rag_search(point_name, top_k=3)
    basic_info = get_acupoint_basic(point_name)
    
    if rag_context and rag_context != "暂无相关知识":
        prompt = f"""请根据以下知识库内容，整理介绍穴位「{point_name}」的详细信息。
【知识库内容】
{rag_context}
请按照以下结构整理：
1. 穴位概述
2. 标准定位
3. 功效主治
4. 操作方法
5. 临床应用心得
6. 注意事项
要求：只基于知识库内容回答，语言清晰专业。
"""
        
        try:
            response = Generation.call(
                model=TEXT_MODEL,
                prompt=prompt,
                temperature=0.5
            )
            detail = response.output.text if response.status_code == 200 else rag_context
        except Exception as e:
            print("query_point_agent调用大模型异常：", str(e))
            detail = rag_context
    else:
        detail = "暂无该穴位的详细知识"
    
    return {
        "success": True,
        "name": point_name,
        "basic_info": basic_info,
        "detail": detail,
        "rag_source": rag_context
    }