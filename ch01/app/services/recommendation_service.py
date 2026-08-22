
from ch01.app.utils.scoring.converter import recommendation_candidate_converter
from ch01.app.repositories.recommendation_repository import TouristSpotRepository
from ch01.app.schemas.recommendation import (
    CandidateSearchRequestToData,
    RecommendationCandidate
)
from ch01.app.database import make_session

from typing import Any


class RecommendationEngine:

    def __init__(self):
        tagSession = make_session()
        embeddingSession = make_session()
        self.repository = TouristSpotRepository(tagSession, embeddingSession)
        
    def __call__(
        self, 
        analyze_info_dict: dict[str, Any]
    ) -> dict[int, RecommendationCandidate]:

        request = self._get_data_from_analysisStore(analyze_info_dict)

        spot_candidate_responses = self.repository.find_scoring_candidates(
            request
        )

        recommendation_candidate_dict = {}

        for candidate in spot_candidate_responses:

            recommendation_candidate = recommendation_candidate_converter(
                candidate,
                request.user_style_tags,
            )
            
            recommendation_candidate_dict[recommendation_candidate.tourist_id] = recommendation_candidate

        return recommendation_candidate_dict
    
    def _get_data_from_analysisStore(
        self, 
        analyze_info_dict: dict[str, Any]
    ) -> CandidateSearchRequestToData:
        
        region_candidate_id_list = analyze_info_dict["candidate_travel_spot_ids"] 
        user_embedding = analyze_info_dict["embedding"]
        user_style_tags = self._extract_user_styleTags(analyze_info_dict["tags"])
        filtered_user_style_tags = self._extract_user_styleTags(analyze_info_dict["filtered_tags"])

        return CandidateSearchRequestToData(
            region_candidate_id_list = region_candidate_id_list,
            user_embedding = user_embedding,
            user_style_tags = user_style_tags,
            filtered_user_style_tags = filtered_user_style_tags
        )   
    
    def _extract_user_styleTags(self, tags: list[dict[str, int | str | float]]) -> dict[str, float]:
        tagsDict: dict[str, float] = {}

        for tag in tags:
            if tag["category"] == "style":
                tagsDict[tag["name"]] = tag["probability"]

        return tagsDict
    
    '''
    def _rank_candidates(
        self,
        candidates: list[RecommendationCandidate],
    ) -> list[RecommendationCandidate]:

        return sorted(
            candidates,
            key=lambda candidate: candidate.recommendation_score,
            reverse=True,
        )
    '''


