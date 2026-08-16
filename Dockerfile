# ==========================================
# Wheretogo backend - Google Cloud Run 용 Dockerfile
# torch/transformers/sentence-transformers가 무겁기 때문에
# torch는 CUDA 없는 CPU 전용 wheel을 먼저 설치해서 이미지 용량을 줄입니다.
# ==========================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # 모델을 앱 시작 시마다 새로 받지 않도록 HF 캐시 위치 고정
    HF_HOME=/app/.cache/huggingface \
    PYTHONPATH=/app:/app/ch01

WORKDIR /app

# psycopg2-binary는 wheel로 설치되므로 별도 libpq-dev는 필요 없지만,
# 일부 패키지 빌드를 위해 최소한의 빌드 도구만 설치합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# requirements 먼저 복사해서 Docker 레이어 캐싱 활용
COPY requirements.txt .

# 1) torch는 CPU 전용 wheel을 명시적으로 먼저 설치 (용량/속도 절약)
# 2) 나머지 requirements 설치 (torch는 버전이 이미 일치하므로 재설치되지 않음)
RUN pip install --upgrade pip && \
    pip install torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

# 앱 코드 복사
COPY . .

# Cloud Run은 컨테이너가 $PORT 환경변수로 지정된 포트를 리슨하길 기대합니다.
# (기본값 8080. Cloud Run이 배포 시 자동으로 PORT를 주입합니다.)
ENV PORT=8080
EXPOSE 8080

# 워커 1개로 시작 (모델을 메모리에 한 번만 올려서 재사용하기 위함).
# 동시 요청이 많아지면 Cloud Run의 concurrency 설정으로 조절하세요.
CMD exec uvicorn ch01.app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
