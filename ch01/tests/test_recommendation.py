from ch01.app.services.recommendation_service import RecommendationEngine
from ch01.app.repositories.recommendation_repository import TouristSpotRepository
from ch01.app import database
from ch01.app.schemas.recommendation import CandidateSearchRequestToData

tagSesstion = database.make_session()
vectorSesstion = database.make_session()

repository = TouristSpotRepository(tagSesstion, vectorSesstion)

engine = RecommendationEngine()

request = CandidateSearchRequestToData(
    region_candidate_id_list=[101, 102, 103],
    user_embedding=[0.01] * 768,  # 실제로는 768차원
    user_style_tags={
        "style_healing": 0.85,
        "style_nature": 0.72,
        "style_activity": 0.41,
        "style_food": 0.68,
    },
    filtered_user_style_tags={
        "style_healing": 0.85,
        "style_nature": 0.72,
    }
)

# type error
#engine(1) 

