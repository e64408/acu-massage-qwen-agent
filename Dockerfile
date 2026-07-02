FROM python:3.7.11-slim

WORKDIR /app

# 只安装依赖，不升级pip（自带版本完全够用，规避源的权限问题）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 用python模块方式启动，彻底避免uvicorn找不到的PATH问题
ENTRYPOINT ["sh", "-c", "python -m uvicorn app:app --host 0.0.0.0 --port 8080"]
