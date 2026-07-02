SAFETY_RULE = {
    "pregnant": ["合谷", "三阴交", "肩井", "昆仑", "至阴"],
    "hypertension": ["百会", "风池", "太冲"]
}

def filter_forbidden_points(name_list, user_condition):
    forbidden = []
    safe_list = []
    for name in name_list:
        if user_condition == "孕妇" and name in SAFETY_RULE["pregnant"]:
            forbidden.append(name)
        elif user_condition == "高血压" and name in SAFETY_RULE["hypertension"]:
            forbidden.append(name)
        else:
            safe_list.append(name)
    return safe_list, forbidden
