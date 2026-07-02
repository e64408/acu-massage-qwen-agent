from PIL import Image, ImageDraw

def draw_weight_heatmap(img_path, point_list, weight_dict, save_path):
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for xn, yn, name in point_list:
        weight = weight_dict[name]
        px = int(xn * w)
        py = int(yn * h)
        radius = int(15 + weight * 55)
        red = int(255 * weight)
        draw.ellipse([px-radius, py-radius, px+radius, py+radius], fill=(red, 20, 20, 160))

    out = Image.alpha_composite(img, overlay).convert("RGB")
    out.save(save_path)
