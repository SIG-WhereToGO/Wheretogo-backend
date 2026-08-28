from fastapi import APIRouter, HTTPException
from sqlalchemy import text, bindparam, Integer, Float, ARRAY

from ch01.app.config.settings import settings
from ch01.app.database import engine
from ch01.app.schemas.info import RecommendSpotInfoFromData, Tag
from ch01.app.schemas.recommendation import RecommendationCandidate
from ch01.app.repositories.repository_error import SpotInfoRepositoryError

import logging

logger = logging.getLogger(__name__)    

def row_to_model(row) -> RecommendSpotInfoFromData:
    detail_info = row.detail_info
    if detail_info == []:
        detail_info = None

    pet_info = row.pet_info
    if pet_info == {}:
        pet_info = None

    tourist_tags = row.tourist_tags
    if tourist_tags == []:
        tourist_tags = None

    tourist_tags_dict = {}

    for tag in (tourist_tags or []):
        tag_model = Tag(
            tag_id = tag["tag_id"],
            category = tag["category"],
            name = tag["name"],
        ) 

        tourist_tags_dict[tag_model.tag_id] = tag_model

    return RecommendSpotInfoFromData(
        recommend_spot_id = row.spot_id,
        name = row.name,
        description = row.description,
        usage_info = row.usage_info,
        detail_info = detail_info,
        region = row.region,
        address = row.address, 
        latitude = float(row.latitude),
        longitude = float(row.longitude), 
        image_url = row.image_url,
        pet_info = pet_info,
        tourism_type = row.tourism_type,
        spot_tags = tourist_tags_dict
    )

def get_spots_Info(
        recommendation_spot_ids: tuple[int]
) -> dict[int, RecommendSpotInfoFromData]:

    tourist_threshold = settings.get_tag_threshold("tourist_description_threshold")

    query = text(
        """
            SELECT
                ts.spot_id AS spot_id,
                ts.name AS name,
                ts.description AS description,
                ts.usage_info AS usage_info,
                ts.detail_info AS detail_info,
                ts.region AS region,
                ts.address AS address,
                ts.latitude AS latitude,
                ts.longitude AS longitude,
                ts.image_url AS image_url,
                ts.content_id AS content_id,
                ts.pet_info AS pet_info,
                ts.tourism_type AS tourism_type,
                jsonb_agg(
                    jsonb_build_object(
                        'tag_id', t.tag_id, 
                        'category', t.category,
                        'name', t.name
                    )
                ) AS tourist_tags
            FROM "TouristSpot" ts
            JOIN "TouristSpotTag" tst
                ON ts.spot_id = tst.spot_id
                AND tst.confidence >= :tourist_threshold
            JOIN "Tag" t
                ON t.tag_id = tst.tag_id
            WHERE ts.spot_id = ANY(:recommendation_spot_ids)
            GROUP BY ts.spot_id;
        """
    ).bindparams(
        bindparam(
            "tourist_threshold",
            type_=Float
        ),
        bindparam(
            "recommendation_spot_ids",
            type_=ARRAY(Integer)
        )
    )

    try:
        with engine.connect() as connection:
            spots_info_list = connection.execute(
                query,
                {
                    "tourist_threshold": tourist_threshold,
                    "recommendation_spot_ids": recommendation_spot_ids
                }
            ).mappings().all()

    except Exception as e:

        logger.exception(
            "ERROR: 관광지 상세 정보 조회 중 DB 오류가 발생했습니다."
        )
        
        raise SpotInfoRepositoryError(
            f"관광지 상세 정보 조회 중 DB 오류 발생: {e}"
        ) from e

    spots_info_dict = {}

    for spot_info in spots_info_list:
        model = row_to_model(spot_info)
        spots_info_dict[model.recommend_spot_id] = model

    return spots_info_dict

