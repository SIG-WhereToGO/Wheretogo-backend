#!/usr/bin/env bash
# ==========================================
# Wheretogo backend - Google Cloud Run 배포 스크립트
#
# 이 스크립트 자체에는 비밀값이 하나도 없습니다.
# deploy.env(gitignore됨)에 있는 모든 KEY=VALUE를 자동으로 읽어서
# Cloud Run 환경변수로 그대로 전달합니다. settings.py에 새 설정값이
# 추가/변경되어도 이 스크립트는 수정할 필요가 없습니다 - deploy.env만
# 채워두면 됩니다.
#
# 사전 준비
#   1) cp deploy.env.example deploy.env  → deploy.env 안의 값 채우기
#      (PROJECT_ID, REGION, SERVICE_NAME은 배포 설정용으로 필수)
#   2) gcloud CLI 설치 + gcloud init + gcloud auth login
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
# shellcheck disable=SC1091
source deploy.env
set +a

if [ -z "${PROJECT_ID:-}" ] || [ -z "${REGION:-}" ] || [ -z "${SERVICE_NAME:-}" ]; then
  echo "deploy.env에 PROJECT_ID / REGION / SERVICE_NAME이 비어 있습니다. 채워주세요."
  exit 1
fi

# ------------------------------------------
# deploy.env의 모든 KEY=VALUE 줄(주석/빈줄 제외)을
# Cloud Run --set-env-vars 형식으로 자동 변환합니다.
# 값 안에 콤마(,)가 있어도 깨지지 않도록 구분자를 "##"로 지정합니다.
# ------------------------------------------
ENV_PAIRS=()
while IFS='=' read -r key _; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  # PROJECT_ID/REGION/SERVICE_NAME은 배포 설정용이라 앱 환경변수에서는 제외
  case "$key" in
    PROJECT_ID|REGION|SERVICE_NAME) continue ;;
  esac
  value="${!key:-}"
  ENV_PAIRS+=("${key}=${value}")
done < <(grep -v '^\s*#' deploy.env | grep '=')

ENV_VARS_STRING=""
for pair in "${ENV_PAIRS[@]}"; do
  if [ -z "$ENV_VARS_STRING" ]; then
    ENV_VARS_STRING="$pair"
  else
    ENV_VARS_STRING="${ENV_VARS_STRING}##${pair}"
  fi
done

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
  --set-env-vars "^##^${ENV_VARS_STRING}"

echo ""
echo "배포 완료. 위 로그의 Service URL로 접속해 테스트하세요."
echo "예: curl https://<service-url>/"
