"""
지역명(예: "해운대", "부산역")으로부터 거리 계산에 사용할 기준 좌표를 가져오는 서비스
==========================================
USER CONFIGURATION
현재는 DB에 저장된 여행지의 이름/주소/지역명을 기반으로 근사 좌표를 찾는 방식입니다.
"해운대"처럼 여행지 DB에 정확히 존재하지 않는 지명(행정동, 역 이름 등)까지 정확하게
처리하려면 카카오/네이버 지도 Geocoding API 등 외부 지오코딩 서비스로 교체하는 것을 권장합니다.
==========================================
"""
from typing import Optional, Tuple

from sqlalchemy import text as sql_text

from ch01.app.database import engine


def get_base_coordinate(region_keyword: str) -> Optional[Tuple[float, float]]:
    """region_keyword를 기준으로 대표 좌표(latitude, longitude)를 반환합니다. 못 찾으면 None."""
    if not region_keyword:
        return None

    try:
        with engine.connect() as connection:
            row = connection.execute(
                sql_text(
                    """
                    SELECT latitude, longitude
                    FROM "TouristSpot"
                    WHERE name ILIKE :kw OR address ILIKE :kw OR region ILIKE :kw
                    LIMIT 1;
                    """
                ),
                {"kw": f"%{region_keyword}%"},
            ).mappings().first()
    except Exception as e:
        raise RuntimeError(f"기준 좌표 조회 실패: {e}") from e

    if row is None or row["latitude"] is None or row["longitude"] is None:
        return None

    return float(row["latitude"]), float(row["longitude"])
