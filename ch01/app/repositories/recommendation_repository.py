#Session + Core/text of SQLAlchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    text,
    bindparam,
    BigInteger,
    Float,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    ARRAY,
)
from sqlalchemy.orm import Session

from ch01.app.schemas.recommendation import (
    SpotCandidateResponseFromData,
    CandidateSearchRequestToData
)

from ch01.app.repositories.repository_error import RecommendationRepositoryError

from concurrent.futures import ThreadPoolExecutor

import logging

logger = logging.getLogger(__name__)

class TouristSpotRepository:

    def __init__(self, tagSession: Session, embeddingSession : Session):
        self.tagSession = tagSession
        self.embeddingSession = embeddingSession

    def row_to_model(self, row) -> SpotCandidateResponseFromData:

        return SpotCandidateResponseFromData.from_db(
            db_tourist_id=row.spot_id,
            db_similarity=float(row.similarity),
            db_style_tags=row.tourist_style_tags,
        )

    def find_styleTag_candidates(
        self,
        request: CandidateSearchRequestToData
    ) -> list[CandidateSearchRequestToData]:

        query = text("""
            SELECT *
            FROM find_tag_candidates(
                :region_candidates,
                :filtered_user_tags,
                :tourist_threshold,
                :user_embedding,
                :set_limit
            )
        """).bindparams(
            bindparam(
                "region_candidates",
                type_=ARRAY(BigInteger)
            ),
            bindparam(
                "filtered_user_tags",
                type_=JSONB
            ),
            bindparam(
                "tourist_threshold",
                type_=Float
            ),
            bindparam(
                "user_embedding",
                type_=Vector(768)
            ),
            bindparam(
                "set_limit",
                type_=BigInteger
            )
        )
        try:
            result = self.tagSession.execute(
                query,
                {
                    "region_candidates": request.region_candidate_id_list,
                    "filtered_user_tags": request.filtered_user_style_tags,
                    "tourist_threshold": request.overview_threshold,
                    "user_embedding": request.user_embedding,
                    "set_limit": request.style_tag_candidates_limit
                }
            )

        except Exception as e:
            self.tagSession.rollback()

            logger.exception(
                "ERROR: Style Tag 후보 조회 중 DB 오류가 발생했습니다."
            )

            raise RecommendationRepositoryError(
                f"An error occurred in the database while retrieving tag-matching candidates: {e}"
            ) from e 

        return [self.row_to_model(row) for row in result]

    
    def find_embedding_candidates(
        self,
        request: CandidateSearchRequestToData
    ) -> list[SpotCandidateResponseFromData]:

        query = text("""
            SELECT *
            FROM find_embedding_candidates(
                :region_candidates,
                :user_embedding,
                :set_limit
            )
        """).bindparams(
            bindparam(
                "region_candidates",
                type_=ARRAY(BigInteger)
            ),
            bindparam(
                "user_embedding",
                type_=Vector(768)
            ),
            bindparam(
                "set_limit",
                type_=BigInteger
            )
        )
        try :
            result = self.embeddingSession.execute(
                query,
                {
                    "region_candidates": request.region_candidate_id_list,
                    "user_embedding": request.user_embedding,
                    "set_limit": request.embedding_candidates_limit
                }
            )
        except Exception as e:
            self.embeddingSession.rollback()

            logger.exception(
                "ERROR: Embedding 후보 조회 중 DB 오류가 발생했습니다."
            )

            raise RecommendationRepositoryError(
                f"An error occurred in the database while retrieving similarity candidates: {e}"
            ) from e 

        return [self.row_to_model(row)  for row in result]

    def merge_candidates(
        self,
        request: CandidateSearchRequestToData,
    ) -> list[SpotCandidateResponseFromData]:

        candidate_map: dict[int, SpotCandidateResponseFromData] = {}

        embedding_candidates: list[SpotCandidateResponseFromData] = []
        styleTag_candidates: list[SpotCandidateResponseFromData] = []

        errors: list[Exception] = []

        with ThreadPoolExecutor(max_workers=2) as executor:

            embedding_future = executor.submit(
                self.find_embedding_candidates,
                request
            )

            styleTag_future = executor.submit(
                self.find_styleTag_candidates,
                request
            )

            # Embedding 작업 결과 확인
            try:
                embedding_candidates = embedding_future.result()

            except Exception as e:
                logger.exception(
                    "ERROR: Embedding 후보 병렬 처리 중 오류가 발생했습니다."
                )
                errors.append(e)

            # Style Tag 작업 결과 확인
            try:
                styleTag_candidates = styleTag_future.result()

            except Exception as e:
                logger.exception(
                    "ERROR: Style Tag 후보 병렬 처리 중 오류가 발생했습니다."
                )
                errors.append(e)

        if errors:
            raise RecommendationRepositoryError(
                f"후보 조회 중 {len(errors)}개의 오류가 발생했습니다."
            ) from errors[0]
    
        for candidate in embedding_candidates:
            candidate_map[candidate.tourist_id] = candidate

        for candidate in styleTag_candidates:
            candidate_map[candidate.tourist_id] = candidate

        return list(candidate_map.values())

    def find_scoring_candidates(
        self,
        request: CandidateSearchRequestToData,
    ) -> list[SpotCandidateResponseFromData]:

        return self.merge_candidates(request)


