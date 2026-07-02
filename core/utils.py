import pandas as pd
import numpy as np
import re
from pathlib import Path

def body_shape_correct(original_xy, height):
    base_height = 165
    scale = height / base_height
    x, y = original_xy
    new_y = np.clip(y * scale, 0.0, 1.0)
    return [round(x, 4), round(new_y, 4)]

def export_points_to_csv(point_data, save_path):
    df = pd.DataFrame(point_data)
    Path(save_path).parent.mkdir(exist_ok=True)
    df.to_csv(save_path, index=False, encoding="utf-8-sig")

def coordinate_range_check(point_xy, standard_range):
    x, y = point_xy
    return standard_range["x_min"] <= x <= standard_range["x_max"] and standard_range["y_min"] <= y <= standard_range["y_max"]

def calculate_confidence(point_xy, standard_range):
    x, y = point_xy
    x_mid = (standard_range["x_min"] + standard_range["x_max"]) / 2
    y_mid = (standard_range["y_min"] + standard_range["y_max"]) / 2
    dx = abs(x - x_mid) / ((standard_range["x_max"] - standard_range["x_min"]) / 2)
    dy = abs(y - y_mid) / ((standard_range["y_max"] - standard_range["y_min"]) / 2)
    dev = max(dx, dy)
    return round(max(0, 100 - dev * 60), 1)

def filter_outlier_points(point_list):
    return [p for p in point_list if p.get("confidence", 60) >= 50]

def normalize_acupoint_name(name: str) -> str:
    # 全局统一清洗规则：去除所有空白、全角空格、"穴"字符
    name = name.strip()
    name = re.sub(r"[穴　 ]", "", name)
    return name

def get_intersection_points(all_recognize_points, target_name_list):
    res = []
    target_set = set(target_name_list)
    for point in all_recognize_points:
        raw_name = point["name"]
        # 复用全局标准化函数，和接口清洗规则完全一致
        clean_name = normalize_acupoint_name(raw_name)
        if clean_name in target_set:
            res.append(point)
    return res