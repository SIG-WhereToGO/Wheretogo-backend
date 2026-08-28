from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel

class Tag(BaseModel):
    tag_id: int
    category: str
    name: str

class RecommendSpotInfoFromData(BaseModel):
    recommend_spot_id: int
    name: str
    description: str
    usage_info: dict[str, str]
    detail_info: Optional[list[dict[str, str]]] = None
    region: str
    address: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    pet_info: Optional[dict[str, str]] = None
    tourism_type: str
    spot_tags: Optional[dict[int, Tag]] = None

class RecommendSpotInfo(BaseModel):
    spot_id: int
    recommendation_score: float
    info: RecommendSpotInfoFromData

class InputAnalysisInfo(BaseModel):
    request_id: str
    input_text: str
    user_tags: dict[int, Tag]
    
    region: Optional[str] = None
    nearby: bool = False
    distance: Optional[float] = None
    unit: Optional[str] = None


class RecommendInfoResponse(BaseModel):
    input_analysis_info: InputAnalysisInfo
    recommend_spots_info: dict[int, RecommendSpotInfo]
    
