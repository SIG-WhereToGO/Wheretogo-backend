from fastapi import FastAPI
from app.routers import spots

app = FastAPI(
    title="어디고 API",
    description="사용자 맞춤형 여행지 추천 서비스 API",
    version="1.0.0"
)

# 여행지 상세 조회 API 연결
app.include_router(spots.router)


@app.get("/")
def root():
    return {
        "message": "어디고 백엔드 서버 정상 실행"
    }