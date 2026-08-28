from fastapi import APIRouter, HTTPException

from ch01.app.schemas.info import RecommendInfoResponse
from ch01.app.services.info_response_service import build_response_infos, sort_response_spots

from ch01.app.stores.store_error import AnalysisResultNotFoundError
from ch01.app.repositories.repository_error import *

from ch01.app.config.settings import settings

import logging

logger = logging.getLogger(__name__)

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
        # 여기서 로그를 안 남기면, 예상 못한 예외는 Cloud Run 로그에
        # 트레이스백 하나 없이 500만 찍혀서 원인 파악이 거의 불가능해집니다.
        logger.exception(
            "ERROR: 추천 정보 조회 중 알 수 없는 오류가 발생했습니다. "
            "analysis_request_id=%s",
            analysis_request_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"추천 정보를 생성하는 중 알 수 없는 오류가 발생했습니다. {e}"
        )from e

