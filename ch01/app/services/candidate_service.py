"""
지역/거리 조건에 따른 여행지 후보군(candidate_travel_spot_ids) 생성 서비스
"""
from typing import List

from ch01.app.repositories import travel_spot_repository
from ch01.app.services.llm_service import RegionCondition
from ch01.app.services.region_service import get_base_coordinate


def build_candidate_ids(condition: RegionCondition) -> List[int]:
    if not condition.region:
        return []

    if condition.nearby and condition.distance:
        base_coordinate = get_base_coordinate(condition.region)
        if base_coordinate is None:
            # 기준 좌표를 못 찾으면 지역명 기반 필터링으로 대체
            return travel_spot_repository.find_ids_by_region(condition.region)

        lat, lon = base_coordinate
        return travel_spot_repository.find_ids_within_radius(lat, lon, condition.distance)

    return travel_spot_repository.find_ids_by_region(condition.region)
