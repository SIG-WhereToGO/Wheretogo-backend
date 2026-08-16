"""
거리 계산 유틸리티
PostGIS를 사용할 수 없는 환경을 위한 Haversine Formula 구현입니다.
(PostGIS를 사용하는 경우 이 함수는 사용되지 않고, DB의 ST_DWithin이 사용됩니다.
 -> ch01/app/repositories/travel_spot_repository.py 참고)
"""
import math

EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표(위도/경도) 사이의 거리를 km 단위로 반환합니다."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c
