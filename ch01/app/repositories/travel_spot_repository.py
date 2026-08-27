"""
여행지 후보군 조회 Repository

"""
from typing import List

from sqlalchemy import text as sql_text

from ch01.app.config.settings import settings
from ch01.app.database import engine
from ch01.app.utils.distance import haversine_distance_km


def find_ids_by_region(region: str) -> List[int]:
    """
    지역명 기준으로 여행지 후보 ID 목록을 조회합니다.

    DB의 region 컬럼은 "시/도 시/군/구" 형식(예: "경기도 광주시")입니다.
    전체 문자열을 통째로 ILIKE '%region%'하면, 시/도와 시/군/구가 이어붙은
    문자열 전체를 대상으로 부분일치를 하게 되어 서로 무관한 지역명이 우연히
    섞여 매칭될 위험이 있습니다. 그래서 공백 기준으로 나눈 토큰(시/도, 시/군/구)
    "안에서만" 부분일치를 검사합니다.
    예) region="경기도 광주시" → 토큰 ["경기도", "광주시"]
        키워드="광주" → "광주시" 토큰과 부분일치 → 매칭 O
        키워드="전남" → 어느 토큰과도 불일치 → 매칭 X

    참고: "광주"(광주광역시 vs 경기도 광주시), "고성"(강원 고성군 vs 경남
    고성군)처럼 실제로 이름이 겹치는 지역은 이 방식으로도 구분되지 않고
    둘 다 후보로 반환됩니다. 이는 버그가 아니라 입력 자체의 모호함을 정직하게
    반영한 것이며, llm_service.py의 프롬프트가 문장에 상위 행정구역이
    같이 언급된 경우 이를 살려서 추출하도록 되어 있어 최대한 완화합니다.
    """
    keyword = f"%{region}%"
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                sql_text(
                    """
                    SELECT spot_id
                    FROM "TouristSpot"
                    WHERE
                        EXISTS (
                            SELECT 1
                            FROM unnest(regexp_split_to_array(region, '\\s+')) AS region_token
                            WHERE region_token ILIKE :keyword
                        )
                        OR region ILIKE :keyword;
                        -- 마지막 조건: LLM이 "경기도 광주시"처럼 여러 단어를
                        -- 통째로 추출해 준 경우까지 대비한 보조 조건입니다.
                    """
                ),
                {"keyword": keyword},
            ).mappings().all()
    except Exception as e:
        raise RuntimeError(f"PostgreSQL 지역 조회 실패: {e}") from e

    return [row["spot_id"] for row in rows]


def find_ids_within_radius_postgis(lat: float, lon: float, radius_km: float) -> List[int]:
    """
    PostGIS ST_DWithin을 이용한 거리 필터링.

    """
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                sql_text(
                    """
                    SELECT spot_id
                    FROM "TouristSpot"
                    WHERE ST_DWithin(
                        geography(ST_MakePoint(longitude, latitude)),
                        geography(ST_MakePoint(:lon, :lat)),
                        :radius_m
                    );
                    """
                ),
                {"lon": lon, "lat": lat, "radius_m": radius_km * 1000},
            ).mappings().all()
    except Exception as e:
        raise RuntimeError(f"PostGIS 거리 조회 실패: {e}") from e

    return [row["spot_id"] for row in rows]


def find_ids_within_radius_haversine(lat: float, lon: float, radius_km: float) -> List[int]:

    try:
        with engine.connect() as connection:
            rows = connection.execute(
                sql_text(
                    """
                    SELECT spot_id, latitude, longitude
                    FROM "TouristSpot"
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
                    """
                )
            ).mappings().all()
    except Exception as e:
        raise RuntimeError(f"PostgreSQL 거리 조회(Haversine) 실패: {e}") from e

    result_ids: List[int] = []
    for row in rows:
        distance = haversine_distance_km(lat, lon, float(row["latitude"]), float(row["longitude"]))
        if distance <= radius_km:
            result_ids.append(row["spot_id"])

    return result_ids


def find_ids_within_radius(lat: float, lon: float, radius_km: float) -> List[int]:

    if settings.use_postgis:
        return find_ids_within_radius_postgis(lat, lon, radius_km)
    return find_ids_within_radius_haversine(lat, lon, radius_km)
