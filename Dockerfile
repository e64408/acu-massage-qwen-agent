FROM python:3.7.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

COPY . .

ENTRYPOINT ["sh", "-c" , "python -m uvicorn app:app --host 0.0.0.0 --port 8080"]
