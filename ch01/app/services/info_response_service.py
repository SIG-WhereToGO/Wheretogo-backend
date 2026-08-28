from ch01.app.schemas.recommendation import RecommendationCandidate
from ch01.app.schemas.info import *
from ch01.app.stores.analysis_store import analysis_store
from ch01.app.stores.store_error import AnalysisResultNotFoundError
from ch01.app.services.recommendation_service import RecommendationEngine
from ch01.app.repositories.spotInfo_repository import get_spots_Info

from concurrent.futures import ThreadPoolExecutor

from typing import Any
import logging

logger = logging.getLogger(__name__)

def _map_score(
    candidate_dict: dict[int, RecommendationCandidate],
    spotInfo_dict: dict[int, RecommendSpotInfoFromData]
) -> dict[int, RecommendSpotInfo]:

    spots_info_dict = {}

    for spot_id, info_from_data in spotInfo_dict.items():
        mapping_info = RecommendSpotInfo(
            spot_id = spot_id,
            info = info_from_data,
            recommendation_score = candidate_dict[spot_id].recommendation_score
        )

        spots_info_dict[spot_id] = mapping_info

    return spots_info_dict

def _create_InputAnalysisInfo_dict(
    analyze_info_dict: dict[str, Any]
) -> InputAnalysisInfo:
    
    filtered_tags_dict = {}
    for tagResult_dict in analyze_info_dict["filtered_tags"]:

        tag = Tag(
            tag_id = tagResult_dict["tag_id"],
            category = tagResult_dict["category"],
            name = tagResult_dict["name"]
        )

        filtered_tags_dict[tag.tag_id] = tag 

    input_info = InputAnalysisInfo (
        request_id = analyze_info_dict["request_id"],
        input_text = analyze_info_dict["input_text"],
        user_tags = filtered_tags_dict,
        
        region = analyze_info_dict["region"],
        nearby = analyze_info_dict["nearby"],
        distance = analyze_info_dict["distance"],
        unit = analyze_info_dict["unit"]
    )

    return input_info

def build_response_infos(
    analysis_request_id: str
) -> RecommendInfoResponse:
    input_analyze_info_dict = analysis_store.get(analysis_request_id)

    if input_analyze_info_dict is None:

        logger.error(
           "ERROR: 분석 결과를 찾을 수 없습니다. "
            + f"analysis_request_id={analysis_request_id}"
        )

        raise AnalysisResultNotFoundError(
            "분석 결과를 찾을 수 없습니다. "
            + f"analysis_request_id={analysis_request_id}"
        )
    
    recommendation_engine = RecommendationEngine()

    errors: list[Exception] = []

    candidate_dict: Optional[dict[int, RecommendationCandidate]] = None
    input_analysis_info: Optional[InputAnalysisInfo] = None

    with ThreadPoolExecutor(max_workers=2) as executor:

        recommendation_future = executor.submit(
            recommendation_engine,
            input_analyze_info_dict
        )

        input_analysis_future = executor.submit(
            _create_InputAnalysisInfo_dict,
            input_analyze_info_dict
        )

        # 추천 엔진 작업
        try:
            candidate_dict = recommendation_future.result()

        except Exception as e:
            logger.exception(
                "ERROR: 추천 엔진 실행 중 오류가 발생했습니다. "
                "analysis_request_id=%s",
                analysis_request_id
            )
            errors.append(e)

        # 사용자 분석 정보 생성 작업
        try:
            input_analysis_info = input_analysis_future.result()

        except Exception as e:
            logger.exception(
                "ERROR: 사용자 분석 정보 생성 중 오류가 발생했습니다. "
                "analysis_request_id=%s",
                analysis_request_id
            )
            errors.append(e)

    if errors:
        # 추천 엔진 또는 사용자 분석 정보 생성 중 실패한 게 있으면,
        # candidate_dict/input_analysis_info가 None인 채로 계속 진행하지 않고
        # (그러면 아래 tuple(candidate_dict) 등에서 "NoneType is not iterable"
        # 같은, 원인을 알 수 없는 2차 에러로 이어지고 원래 에러 로그도 묻힙니다)
        # 실제 원인이 된 예외를 그대로 다시 발생시킵니다.
        raise errors[0]

    recommendation_spot_ids = tuple(candidate_dict)
    spotInfo_dict = get_spots_Info(recommendation_spot_ids)

    mapping_recommendation_spots_info_dict = _map_score(
        candidate_dict = candidate_dict,
        spotInfo_dict = spotInfo_dict
    )

    response = RecommendInfoResponse(
        input_analysis_info=input_analysis_info,
        recommend_spots_info=mapping_recommendation_spots_info_dict
    )

    return response

def sort_response_spots(
    response: RecommendInfoResponse,
    sort_standard: str = "recommendation_score"
) -> RecommendInfoResponse:

    sorted_list = sorted(
        response.recommend_spots_info.items(),
        key=lambda item: getattr(item[1], sort_standard),
        reverse=True
    )

    sorted_dict ={}

    for tuple_item in sorted_list:
        key = tuple_item[0]
        value = tuple_item[1]
        sorted_dict[key] = value

    response.recommend_spots_info = sorted_dict

    return response