from dataclasses import dataclass
from ch01.app.schemas.tags import TOURIST_STYLE_TAGS
from ch01.app.config.settings import settings
from typing import ClassVar
import logging

logger = logging.getLogger(__name__)

#toData
@dataclass
class CandidateSearchRequestToData:
    region_candidate_id_list: list[int]
    user_embedding: list[float]
    user_style_tags: dict[str, float]
    filtered_user_style_tags: dict[str, float]
    
    overview_threshold: ClassVar[float] = settings.get_tag_threshold(
        "tourist_description_threshold"
    )
    user_input_threshold: ClassVar[float] = settings.get_tag_threshold(
        "user_input_threshold"
    )
    
    embedding_candidates_limit: ClassVar[int] = settings.vector_filter_limit
    style_Tag_candidates_limit: ClassVar[int] = settings.style_Tag_filter_limit


#toService
@dataclass
class SpotCandidateResponseFromData:
    tourist_id: int
    similarity: float
    tourist_style_tags: tuple[float, ...]

    @staticmethod
    def validate_db_tourist_style_tags(
        v_db_tourist_id: int,
        v_db_tourist_style_tags: dict[str, float],
    ) -> None:

        missing_tags = set(TOURIST_STYLE_TAGS) - v_db_tourist_style_tags.keys()

        if missing_tags:
            logger.error(
                "ERROR: "
                "관광지 스타일 태그 검증 실패. "
                "tourist_id=%s, missing_tags=%s",
                v_db_tourist_id,
                missing_tags,
            )
            
            raise ValueError(
                f"Missing style tags (id {v_db_tourist_id}): {missing_tags}"
            )

    @classmethod
    def from_db(
        my_class,
        db_tourist_id: int,
        db_similarity: float,
        db_style_tags: dict[str, float],
    ):
        my_class.validate_db_tourist_style_tags(
            v_db_tourist_id=db_tourist_id,
            v_db_tourist_style_tags=db_style_tags
        )

        return my_class(
            tourist_id=db_tourist_id,
            similarity=db_similarity,
            tourist_style_tags=tuple(
                db_style_tags.get(label)
                for label in TOURIST_STYLE_TAGS
            ),
        )

@dataclass
class RecommendationCandidate:
    tourist_id: int
    recommendation_score: float
    