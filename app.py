import os
import json
import time
import zipfile
import uuid
from pathlib import Path
from PIL import Image
# 修复点：统一在顶部导入JSONResponse，不再函数内导入
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 接收前端提交key的请求体模型
class KeySubmitReq(BaseModel):
    api_key: str

from agents.acupoint_agent import run_vision_agent
from agents.symptom_agent import run_symptom_agent
from core.tsp import build_robot_task_path, draw_robot_trajectory
from core.heatmap import draw_weight_heatmap
from core.memory import init_db, save_record, get_statistics
from core.utils import export_points_to_csv, get_intersection_points, normalize_acupoint_name

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)

BASE_WEIGHT_MAP = {"足三里": 0.9, "三阴交": 0.85, "合谷": 0.8, "内关": 0.75}
DEFAULT_WEIGHT = 0.4

init_db()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")
templates = Jinja2Templates(directory="templates")

# 清空密钥Cookie接口
@app.post("/api/clear_key")
async def clear_key(response: Response):
    response.set_cookie(
        key="DASHSCOPE_API_KEY",
        value="",
        max_age=0,
        httponly=True,
        samesite="lax"
    )
    return {"code": 200, "msg": "清除完成"}

# 校验密钥是否存在
@app.get("/api/check_key")
async def check_key(request: Request):
    current_key = request.cookies.get("DASHSCOPE_API_KEY", "")
    return {"has_key": bool(current_key.strip())}

# 提交密钥写入会话Cookie（仅当前标签存活有效）
@app.post("/api/set_qwen_key")
async def set_qwen_key(req: KeySubmitReq):
    input_key = req.api_key.strip()
    if not input_key.startswith("sk-"):
        raise HTTPException(status_code=400, detail="密钥格式错误，必须以 sk- 开头")
    # 直接使用顶部已导入的JSONResponse，无函数内import
    resp = JSONResponse(content={"code": 200, "msg": "密钥提交成功"})
    resp.set_cookie(
        key="DASHSCOPE_API_KEY",
        value=input_key,
        httponly=True,
        max_age=None,
        samesite="lax"
    )
    return resp

# 首页：每次访问立刻删除密钥Cookie
@app.get("/", response_class=HTMLResponse)
async def index(response: Response):
    response.set_cookie(
        key="DASHSCOPE_API_KEY",
        value="",
        max_age=0,
        httponly=True,
        samesite="lax"
    )
    return templates.TemplateResponse("index.html", {"request": {}})

# 图像识别
@app.post("/api/image-rec")
async def image_rec(
    request: Request,
    file: UploadFile = File(...),
    height: int = Form(165),
    health_condition: str = Form("无")
):
    user_api_key = request.cookies.get("DASHSCOPE_API_KEY", "").strip()
    if not user_api_key:
        raise HTTPException(status_code=401, detail="未填写密钥，请刷新页面重新输入")

    try:
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in ["jpg", "jpeg", "png"]:
            return {"error": "仅支持jpg、png图片"}

        file_id = uuid.uuid4().hex
        save_path = UPLOAD_DIR / f"{file_id}.{ext}"
        with open(save_path, "wb") as f:
            f.write(await file.read())

        img = Image.open(save_path)
        w, h = img.size

        point_list, check_log, llm_raw_text = run_vision_agent(
            str(save_path),
            user_api_key=user_api_key,
            user_height=height,
            health_condition=health_condition
        )

        full_point_list = []
        mid_single_acu = ["百会","印堂","人中","大椎","命门","腰阳关","膻中","中脘","神阙","气海","关元"]
        for p in point_list:
            full_point_list.append(p)
            point_name = p.get("name", "")
            if point_name in mid_single_acu:
                continue
            mirror_item = {
                "x": round(1 - p["x"], 4),
                "y": round(1 - p["y"], 4),
                "name": point_name,
                "confidence": p["confidence"]
            }
            full_point_list.append(mirror_item)
        point_list = full_point_list

        xy_only = [(p["x"], p["y"], p.get("name", "未知穴位")) for p in point_list]
        robot_task, sorted_xy = build_robot_task_path(xy_only, w, h, base_duration=3)

        traj_name = f"{uuid.uuid4().hex}_traj.jpg"
        draw_robot_trajectory(str(save_path), sorted_xy, str(OUT_DIR / traj_name))

        heat_name = f"{uuid.uuid4().hex}_heat.jpg"
        weight_dict = {name: BASE_WEIGHT_MAP.get(name, DEFAULT_WEIGHT) for _, _, name in sorted_xy}
        draw_weight_heatmap(str(save_path), sorted_xy, weight_dict, str(OUT_DIR / heat_name))

        export_points_to_csv(robot_task, str(OUT_DIR / "robot_points.csv"))

        return {
            "qwen_raw_reply": llm_raw_text,
            "points": point_list,
            "check_result": check_log,
            "robot_task": robot_task,
            "trajectory_img": f"/output/{traj_name}",
            "heatmap_img": f"/output/{heat_name}",
            "img_width": w,
            "img_height": h,
            "img_file_id": f"{file_id}.{ext}",
            "status": "ok"
        }
    except Exception as e:
        import traceback
        err_stack = traceback.format_exc()
        print("【/api/image-rec 异常】\n", err_stack)
        return {"error": f"图像识别异常：{str(e)}"}

# 辨证接口
@app.post("/api/filter-by-symptom")
async def filter_by_symptom(
    request: Request,
    all_points_json: str = Form(...),
    img_file_id: str = Form(...),
    img_w: int = Form(...),
    img_h: int = Form(...),
    part: str = Form(...),
    symptom: str = Form(...),
    level: str = Form(...),
    condition: str = Form(...)
):
    user_api_key = request.cookies.get("DASHSCOPE_API_KEY", "").strip()
    if not user_api_key:
        raise HTTPException(status_code=401, detail="未填写密钥，请刷新页面重新输入")

    try:
        all_points = json.loads(all_points_json)
        if not all_points:
            return {"error": "请先识别图片"}
        if not symptom.strip():
            return {"error": "请选择症状"}

        img_path = str(UPLOAD_DIR / img_file_id)
        match_key = f"{part}-{symptom}"
        print("匹配关键词：", match_key)
        rag_result = run_symptom_agent(match_key, condition)
        print("辨证结果：", rag_result)

        plan_data = rag_result.get("full_plan", {})
        plan_description = plan_data.get("description", "暂无简介")
        plan_detail = plan_data.get("detail", "暂无说明")
        plan_order = plan_data.get("order", [])
        plan_all_points = plan_data.get("points", [])

        raw_safe_list = rag_result.get("safe_point_list", [])
        treat_names = []
        for n in raw_safe_list:
            real_name = n.get("name", "") if isinstance(n, dict) else str(n)
            clean_name = normalize_acupoint_name(real_name)
            if clean_name.strip():
                treat_names.append(clean_name)

        filtered_points = get_intersection_points(all_points, treat_names)
        if len(filtered_points) == 0:
            filtered_points = all_points

        level_coeff = {"轻度":0.6,"中度":1.0,"重度":1.6}[level]
        duration = round(3 * level_coeff)

        xy_only = [(p["x"], p["y"], p.get("name", "未知穴位")) for p in filtered_points]
        robot_task, sorted_xy = build_robot_task_path(xy_only, img_w, img_h, base_duration=duration)

        traj_name = f"{uuid.uuid4().hex}_traj.jpg"
        draw_robot_trajectory(img_path, sorted_xy, str(OUT_DIR / traj_name))

        heat_name = f"{uuid.uuid4().hex}_heat.jpg"
        weight_dict = {}
        for _, _, name in sorted_xy:
            base = BASE_WEIGHT_MAP.get(name, DEFAULT_WEIGHT)
            weight_dict[name] = min(base * level_coeff, 1.0)
        draw_weight_heatmap(img_path, sorted_xy, weight_dict, str(OUT_DIR / heat_name))

        point_names = [p.get("name", "未知穴位") for p in filtered_points]
        save_record(time.strftime("%Y-%m-%d %H:%M:%S"), f"{part}-{symptom}-{level}", point_names, json.dumps(robot_task, ensure_ascii=False))
        export_points_to_csv(robot_task, str(OUT_DIR / "robot_points.csv"))

        return {
            "points": filtered_points,
            "robot_task": robot_task,
            "trajectory_img": f"/output/{traj_name}",
            "heatmap_img": f"/output/{heat_name}",
            "plan_description": plan_description,
            "plan_detail": plan_detail,
            "plan_order": plan_order,
            "plan_all_points": plan_all_points,
            "status": "ok"
        }
    except Exception as e:
        import traceback
        err_stack = traceback.format_exc()
        print("【/api/filter-by-symptom 异常】\n", err_stack)
        return {"error": f"辨证异常：{str(e)}"}

# 统计、导出接口
@app.get("/api/stat-data")
async def stat_data():
    try:
        return {"frequency_count": get_statistics()}
    except Exception as e:
        import traceback
        err_stack = traceback.format_exc()
        print("统计接口异常\n", err_stack)
        return {"error": f"加载统计失败：{str(e)}"}

@app.get("/download-csv")
async def download_csv():
    return FileResponse(str(OUT_DIR / "robot_points.csv"), filename="机器人点位.csv")

@app.get("/download-all")
async def download_all():
    zip_name = f"成果_{uuid.uuid4().hex}"
    zip_path = OUT_DIR / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in OUT_DIR.glob("*.*"):
            if f.suffix in [".jpg", ".png", ".csv"]:
                zf.write(f, arcname=f.name)
    return FileResponse(str(zip_path), filename=f"{zip_name}.zip")