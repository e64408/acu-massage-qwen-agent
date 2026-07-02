import numpy as np
from PIL import Image, ImageDraw, ImageFont

def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def tsp_greedy(points):
    if len(points) <= 1:
        return points
    path = [points[0]]
    unvisited = points[1:]
    while unvisited:
        next_p = min(unvisited, key=lambda p: distance(path[-1], p))
        path.append(next_p)
        unvisited.remove(next_p)
    return path

def build_robot_task_path(point_list, img_width, img_height, base_duration=3):
    sorted_points = tsp_greedy(point_list)
    task_list = []
    for idx, (x_norm, y_norm, name) in enumerate(sorted_points):
        task_list.append({
            "step": idx + 1,
            "point_name": name,
            "norm_x": x_norm,
            "norm_y": y_norm,
            "massage_seconds": base_duration
        })
    return task_list, sorted_points

def draw_robot_trajectory(img_path, sorted_point_xy, save_path):
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    try:
        font = ImageFont.truetype("simhei.ttf", 14)
    except:
        try:
            font = ImageFont.truetype("Arial Unicode.ttf", 14)
        except:
            font = ImageFont.load_default()

    pixels = []
    for xn, yn, _ in sorted_point_xy:
        px = int(xn * w)
        py = int(yn * h)
        pixels.append((px, py))
    if len(pixels) > 1:
        draw.line(pixels, fill="#ff2222", width=3)

    for i, (px, py) in enumerate(pixels):
        r = 8
        draw.ellipse((px - r, py - r, px + r, py + r), fill="#ff0000")
        draw.text((px + 10, py), str(i + 1), fill="#000000", font=font)
    img.save(save_path)
