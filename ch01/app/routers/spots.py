from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ch01.app.database import engine


router = APIRouter(
    prefix="/api/spots",
    tags=["여행지 상세 조회"]
)


@router.get("/{spot_id}")
def get_spot_detail(spot_id: int):

    with engine.connect() as connection:

        # 1. 관광지 기본/상세 정보 조회
        spot = connection.execute(
            text("""
                SELECT
                    spot_id,
                    name,
                    description,
                    usage_info,
                    detail_info,
                    region,
                    address,
                    latitude,
                    longitude,
                    image_url,
                    content_id,
                    pet_info,
                    tourism_type
                FROM "TouristSpot"
                WHERE spot_id = :spot_id;
            """),
            {
                "spot_id": spot_id
            }
        ).mappings().first()

        # 2. 존재하지 않는 관광지
        if spot is None:
            raise HTTPException(
                status_code=404,
                detail="해당 여행지를 찾을 수 없습니다."
            )

        # 3. 해당 관광지 태그 조회
        tag_rows = connection.execute(
            text("""
                SELECT
                    t.tag_id,
                    t.name,
                    t.category,
                    tst.confidence
                FROM "TouristSpotTag" tst
                JOIN "Tag" t
                    ON tst.tag_id = t.tag_id
                WHERE tst.spot_id = :spot_id
                ORDER BY t.tag_id;
            """),
            {
                "spot_id": spot_id
            }
        ).mappings().all()

    # 4. 프론트로 보낼 JSON 구성
    return {
        "spot_id": spot["spot_id"],
        "name": spot["name"],
        "description": spot["description"],
        "region": spot["region"],
        "address": spot["address"],
        "latitude": spot["latitude"],
        "longitude": spot["longitude"],
        "image_url": spot["image_url"],
        "usage_info": spot["usage_info"],
        "detail_info": spot["detail_info"],
        "pet_info": spot["pet_info"],
        "tourism_type": spot["tourism_type"],
        "content_id": spot["content_id"],
        "tags": [
            {
                "tag_id": tag["tag_id"],
                "name": tag["name"],
                "category": tag["category"],
                "confidence": tag["confidence"]
            }
            for tag in tag_rows
        ]
    }