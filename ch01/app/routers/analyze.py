"""
POST /analyze

"""
from fastapi import APIRouter, HTTPException, Body

from ch01.app.config.settings import settings
from ch01.app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from ch01.app.services.analyze_service import analyze

router = APIRouter(tags=["여행 요구사항 분석"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_travel_request(payload: AnalyzeRequest):
    input_text = payload.input_text.strip()

    # 입력문이 지나치게 긴 경우
    if len(input_text) > settings.max_input_length:
        raise HTTPException(
            status_code=422,
            detail=f"입력문이 너무 깁니다. 최대 {settings.max_input_length}자까지 입력 가능합니다.",
        )

    try:
        result = analyze(input_text)
    except RuntimeError as e:
        detail = str(e)

        # 모델이 아직 로딩되지 않았거나 로딩 자체에 실패한 경우 -> 서버 준비 안됨
        if "모델이 아직 로딩되지 않았습니다" in detail or "모델 로딩 실패" in detail:
            raise HTTPException(status_code=503, detail=detail) from e

        # 모델 inference 실패 -> 서버 내부 오류
        if "inference 실패" in detail:
            raise HTTPException(status_code=500, detail=detail) from e

        # LLM API 호출/파싱 실패 -> 외부 연동 오류 (Bad Gateway)
        if "LLM API" in detail or "지역 추출 실패" in detail:
            raise HTTPException(status_code=502, detail=detail) from e

        # PostgreSQL / PostGIS / 좌표 조회 / 태그 매핑 실패 -> 서비스 이용 불가
        if any(
            keyword in detail
            for keyword in ["PostgreSQL", "PostGIS", "좌표 조회", "태그 매핑"]
        ):
            raise HTTPException(status_code=503, detail=detail) from e

        # 분석 결과 임시 저장 실패 -> 서버 내부 오류
        if "임시 저장" in detail:
            raise HTTPException(status_code=500, detail=detail) from e

        raise HTTPException(status_code=500, detail=detail) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알 수 없는 서버 오류: {e}") from e

    return result
