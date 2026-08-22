"""
여행지 후보군 조회 Repository

"""
from typing import List

from sqlalchemy import text as sql_text

from ch01.app.config.settings import settings
from ch01.app.database import engine
from ch01.app.utils.distance import haversine_distance_km


def find_ids_by_region(region: str) -> List[int]:
    """지역명 기준으로 여행지 후보 ID 목록을 조회합니다."""
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                sql_text(
                    """
                    SELECT spot_id
                    FROM "TouristSpot"
                    WHERE region ILIKE :region;
                    """
                ),
                {"region": f"%{region}%"},
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
