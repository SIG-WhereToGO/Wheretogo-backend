from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# 신규 POST /analyze API 관련 import
# (기존 app.routers.spots / database 로직은 전혀 수정하지 않았습니다)
# ==========================================
from ch01.app.config.settings import settings
from ch01.app.database import engine
from ch01.app.models.klue_roberta import klue_roberta_model
from ch01.app.models.sbert import sbert_model
from ch01.app.routers import analyze, recommendation_Info
from ch01.app.stores.analysis_store import analysis_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Server Start
      -> KLUE-RoBERTa Load
      -> SBERT Load
      -> DB Connection 확인
      -> Analysis Store 초기화(TTL 설정)
      -> Server Ready
    """

    klue_roberta_model.load()
    sbert_model.load()

    # DB 연결 확인 (기존 database.py의 engine을 그대로 재사용합니다)
    with engine.connect():
        pass

    analysis_store.set_ttl_minutes(settings.analysis_ttl_minutes)

    yield

    # 서버 종료 시 별도로 정리할 리소스는 현재 없습니다.


app = FastAPI(
    title="어디고 API",
    description="사용자 맞춤형 여행지 추천 서비스 API",
    version="1.0.0",
    lifespan=lifespan
)

# ==========================================
# CORS 설정
# 프론트가 백엔드와 다른 도메인(예: netlify.app)에서 API를 호출하려면
# 그 도메인이 여기 허용 목록(ALLOWED_ORIGINS 환경변수)에 있어야 합니다.
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 여행 요구사항 분석 API 연결 (POST /analyze) - 신규 추가
app.include_router(analyze.router)

# 여행지 상세 조회 API 연결
app.include_router(recommendation_Info.router)

@app.get("/")
def root():
    return {
        "message": "어디고 백엔드 서버 정상 실행"
    }
