from ch01.app.schemas.recommendation import (
    SpotCandidateResponseFromData,
    RecommendationCandidate
)
from ch01.app.schemas.tags import TOURIST_STYLE_TAGS as standard
from ch01.app.utils.scoring.calculator import (
    calculate_soft_f1, 
    calculate_recommendation_score
)

def convert_to_Tuple(standard: tuple[str, ...], data: dict[str, float]) -> tuple[float, ...]:
    return tuple(data.get(key) for key in standard)

def recommendation_candidate_converter(
    scoring_model: SpotCandidateResponseFromData,
    user_style_tags: dict[str, float]
) -> RecommendationCandidate:
    
    tourist_id = scoring_model.tourist_id
    similarity = scoring_model.similarity

    tourist_style_tagDic = scoring_model.tourist_style_tags
    user_style_tagDic = user_style_tags
    tourist_style_tagTuple = convert_to_Tuple(standard, tourist_style_tagDic)
    user_style_tagTuple = convert_to_Tuple(standard, user_style_tagDic)

    soft_f1 = calculate_soft_f1 (
        user_style_tags = user_style_tagTuple,
        tourist_style_tags = tourist_style_tagTuple
    )

    recommendation_score = calculate_recommendation_score (
        tag_score = soft_f1,
        similarity = similarity
    )

    return RecommendationCandidate(
            tourist_id = tourist_id,
            recommendation_score = recommendation_score,
    )

    
   
