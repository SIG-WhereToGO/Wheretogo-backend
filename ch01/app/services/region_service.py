"""
지역명(예: "해운대", "부산역")으로부터 거리 계산에 사용할 기준 좌표를 가져오는 서비스

"""
from typing import Optional, Tuple

from sqlalchemy import text as sql_text

from ch01.app.database import engine


def get_base_coordinate(region_keyword: str) -> Optional[Tuple[float, float]]:
    
    if not region_keyword:
        return None

    keyword = f"%{region_keyword}%"
    try:
        with engine.connect() as connection:
            row = connection.execute(
                sql_text(
                    """
                    SELECT latitude, longitude
                    FROM "TouristSpot"
                    WHERE
                        name ILIKE :keyword
                        OR address ILIKE :keyword
                        OR EXISTS (
                            SELECT 1
                            FROM unnest(regexp_split_to_array(region, '\\s+')) AS region_token
                            WHERE region_token ILIKE :keyword
                        )
                    ORDER BY
                        -- 더 구체적인 필드(이름/주소)에서 매칭된 경우를 우선시합니다.
                        CASE
                            WHEN name ILIKE :keyword THEN 0
                            WHEN address ILIKE :keyword THEN 1
                            ELSE 2
                        END
                    LIMIT 1;
                    """
                ),
                {"keyword": keyword},
            ).mappings().first()
    except Exception as e:
        raise RuntimeError(f"기준 좌표 조회 실패: {e}") from e

    if row is None or row["latitude"] is None or row["longitude"] is None:
        return None

    return float(row["latitude"]), float(row["longitude"])
