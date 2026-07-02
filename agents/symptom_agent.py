from core.rag import get_rag_instance

def run_symptom_agent(query: str, health_condition: str):
    rag = get_rag_instance()
    kb_result = rag.search(query)
    
    # 修复点：使用 .get() 防止KeyError
    name_list = [item.get("name", "") for item in kb_result]
    name_list = [n for n in name_list if n.strip()]

    # 禁忌过滤逻辑不变
    forbidden = []
    if health_condition == "孕妇":
        forbidden = ["合谷", "三阴交", "肩井"]
    elif health_condition == "高血压":
        forbidden = ["涌泉", "百会"]
    
    safe_point_list = [n for n in name_list if n not in forbidden]
    presc_data = rag.prescription_map.get(query, {})

    return {
        "safe_point_list": safe_point_list,
        "full_plan": {
            "description": presc_data.get("description", ""),
            "detail": presc_data.get("detail", ""),
            "order": safe_point_list,
            "points": safe_point_list
        }
    }