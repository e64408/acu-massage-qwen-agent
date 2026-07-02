import json
import re
import dashscope  # 新增导入
from dashscope import MultiModalConversation
from core.rag import get_rag_instance
from core.utils import body_shape_correct, calculate_confidence, filter_outlier_points
from core.safety_rule import filter_forbidden_points

def strip_json_markdown(text: str) -> str:
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.S)
    if match:
        return match.group(1)
    return text

# 新增 user_api_key 入参
def run_vision_agent(img_path: str, user_api_key: str, user_height=165, health_condition="无"):
    # 函数最开头强制设置本次请求密钥，底层上传、VL调用全部生效
    dashscope.api_key = user_api_key
    
    rag_engine = get_rag_instance()

    response = MultiModalConversation.call(
        model="qwen-vl-max",
        messages=[
            {
                "role": "user",
                "content": [
                    {"image": f"file://{img_path}"},
                    {
                        "text": """
任务：识别人体解剖图上全部中医针灸穴位
规则：
1. 只输出国家标准中医穴位名称（如大椎、肩井、天宗、肺俞、肾俞、委中、足三里、合谷、内关、三阴交）；
2. 禁止输出肌肉、骨骼、脊柱、肩胛骨、斜方肌、后背、腰背、颈椎、腰椎这类解剖组织名词；
3. 每个点位必须对应真实针灸穴位，不许编造解剖部位；
4. 输出格式仅纯JSON数组，不要markdown、不要任何解释文字；
5. 每条JSON字段：name(穴位名),x(归一化0~1横坐标),y(归一化0~1纵坐标)
"""
                    }
                ]
            }
        ]
    )
    raw_text = response.output.choices[0].message.content[0]["text"]
    clean_text = strip_json_markdown(raw_text)

    try:
        point_list = json.loads(clean_text)
    except Exception:
        point_list = []

    # 新增：过滤肌肉骨骼类无效点位，兜底防止匹配失败
    black_word = ["脊柱", "肩胛骨", "斜方肌", "骨骼", "肌肉", "后背", "腰背", "颈椎", "腰椎"]
    valid_list = []
    for item in point_list:
        if "name" in item and item["name"] not in black_word:
            valid_list.append(item)
    point_list = valid_list

    raw_names = [p["name"] for p in point_list]
    safe_names, _ = filter_forbidden_points(raw_names, health_condition)

    final_points = []
    check_log = []
    for p in point_list:
        if p["name"] not in safe_names:
            continue
        name = p["name"]
        xy = [p["x"], p["y"]]
        new_xy = body_shape_correct(xy, user_height)
        ok, range_info = rag_engine.verify_point_coordinate(name, new_xy)
        score = calculate_confidence(new_xy, range_info) if range_info else 60

        check_log.append({"point": name, "in_standard_range": ok, "confidence_score": score})
        final_points.append({
            "name": name,
            "x": new_xy[0],
            "y": new_xy[1],
            "valid": ok,
            "confidence": score
        })

    final_points = filter_outlier_points(final_points)
    return final_points, check_log, raw_text