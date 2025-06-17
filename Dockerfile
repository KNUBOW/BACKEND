# python 이미지 설치 v3.10
FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# 라이브러리 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 도커 시간대 설정 -> 한국 시간대로
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime && \
    echo "Asia/Seoul" > /etc/timezone && \
    apt-get clean

# 5️⃣ 프로젝트 전체 복사
COPY . .

# 6️⃣ 환경 변수 설정
ENV PYTHONPATH=/app/src

# 7️⃣ FastAPI 실행
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--lifespan", "on"]
