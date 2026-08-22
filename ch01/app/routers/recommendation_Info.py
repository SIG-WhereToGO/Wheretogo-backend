from fastapi import APIRouter, HTTPException

from ch01.app.schemas.info import RecommendInfoResponse
from ch01.app.services.info_response_service import build_response_infos, sort_response_spots

from ch01.app.stores.store_error import AnalysisResultNotFoundError
from ch01.app.repositories.repository_error import *

from ch01.app.config.settings import settings

router = APIRouter(
    prefix="/api/recommendations",
    tags=["여행지 상세 조회"]
)

@router.get(
    "/{analysis_request_id}",
    response_model=RecommendInfoResponse
)
def get_recommendation_information(
    analysis_request_id: str,
    page: int = 1,
    size: int = settings.final_top_n,
    sort: str = "recommendation_score" 
) -> RecommendInfoResponse:
    try:
        infos = build_response_infos(analysis_request_id)

        return sort_response_spots(infos, sort)
    
    except AnalysisResultNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )from e

    except RecommendationRepositoryError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )from e

    except SpotInfoRepositoryError as e:
         raise HTTPException(
            status_code=503,
            detail=str(e)
        )from e
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"추천 정보를 생성하는 중 알 수 없는 오류가 발생했습니다. {e}"
        )from e

