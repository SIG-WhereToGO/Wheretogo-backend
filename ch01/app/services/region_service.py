"""
지역명(예: "해운대", "부산역")으로부터 거리 계산에 사용할 기준 좌표를 가져오는 서비스

"""
from typing import Optional, Tuple

from sqlalchemy import text as sql_text

from ch01.app.database import engine


def get_base_coordinate(region_keyword: str) -> Optional[Tuple[float, float]]:
    """region_keyword를 기준으로 대표 좌표(latitude, longitude)를 반환. 못 찾으면 None."""
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
