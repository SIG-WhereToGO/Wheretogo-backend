#!/usr/bin/env bash
# ==========================================
# Wheretogo backend - Google Cloud Run 배포 스크립트
#
# 사전 준비
#   1) https://console.cloud.google.com 에서 프로젝트 생성 (신용카드 등록 필요,
#      Always Free 한도 안에서는 과금되지 않음)
#   2) gcloud CLI 설치 후 `gcloud init` / `gcloud auth login`
#   3) 아래 "USER CONFIGURATION" 값들을 채우기
#
# 사용법
#   chmod +x scripts/deploy_cloudrun.sh
#   ./scripts/deploy_cloudrun.sh
# ==========================================
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f "deploy.env" ]; then
  echo "deploy.env 파일이 없습니다. 먼저 실행하세요: cp deploy.env.example deploy.env"
  echo "그 다음 deploy.env를 열어 실제 값을 채워주세요."
  exit 1
fi

# deploy.env의 KEY=VALUE 줄들을 환경변수로 불러옴
set -a
source deploy.env
set +a

gcloud config set project "${PROJECT_ID}"

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 1 \
  --concurrency 4 \
  --timeout 300 \
  --set-env-vars "KLUE_MODEL_PATH=${KLUE_MODEL_PATH}" \
  --set-env-vars "KLUE_TOKENIZER_PATH=${KLUE_TOKENIZER_PATH}" \
  --set-env-vars "SBERT_MODEL_PATH=${SBERT_MODEL_PATH}" \
  --set-env-vars "HF_TOKEN=${HF_TOKEN}" \
  --set-env-vars "DATABASE_URL=${DATABASE_URL}" \
  --set-env-vars "LLM_API_KEY=${LLM_API_KEY}" \
  --set-env-vars "LLM_API_BASE_URL=${LLM_API_BASE_URL}" \
  --set-env-vars "LLM_MODEL_NAME=${LLM_MODEL_NAME}" \
  --set-env-vars "DEFAULT_RADIUS_KM=${DEFAULT_RADIUS_KM}" \
  --set-env-vars "TAG_THRESHOLD=${TAG_THRESHOLD}" \
  --set-env-vars "ANALYSIS_TTL_MINUTES=${ANALYSIS_TTL_MINUTES}" \
  --set-env-vars "USE_POSTGIS=${USE_POSTGIS}" \
  --set-env-vars "MAX_INPUT_LENGTH=${MAX_INPUT_LENGTH}"

echo ""
echo "배포 완료. 위 로그의 Service URL로 접속해 테스트하세요."
echo "예: curl https://<service-url>/"
