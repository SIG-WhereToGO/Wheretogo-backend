"""
POST /analyze 전체 파이프라인을 조율하는 서비스

사용자 입력
  -> KLUE-RoBERTa (태그 추출)
  -> SBERT (embedding 생성)
  -> LLM API (지역/거리 조건 추출)
  -> PostgreSQL (지역/거리 조건에 따른 후보 여행지 조회)
  -> 서버 메모리 임시 저장
  -> request_id + region + tags 반환
"""
import uuid
from typing import List

from ch01.app.schemas.analyze import TagResult
from ch01.app.services import candidate_service, embedding_service, tag_service
from ch01.app.services.llm_service import extract_region_condition
from ch01.app.stores.analysis_store import analysis_store


def analyze(input_text: str) -> dict:
    # 1. KLUE-RoBERTa 태그 추출
    tags: List[TagResult] = tag_service.extract_tags(input_text)

    # 2. SBERT embedding 생성
    embedding = embedding_service.generate_embedding(input_text)

    # 3. LLM API로 지역/거리 조건 추출
    condition = extract_region_condition(input_text)

    # 4. 지역/거리 조건에 따른 여행지 후보군 조회
    candidate_ids = candidate_service.build_candidate_ids(condition)

    # 5. 분석 결과 서버 메모리에 임시 저장
    request_id = str(uuid.uuid4())
    try:
        analysis_store.set(
            request_id,
            {
                "request_id": request_id,
                "input_text": input_text,
                "tags": [tag.model_dump() for tag in tags],
                "embedding": embedding,
                "region": condition.region,
                "nearby": condition.nearby,
                "distance": condition.distance,
                "unit": condition.unit,
                "candidate_travel_spot_ids": candidate_ids,
            },
        )
    except Exception as e:
        raise RuntimeError(f"분석 결과 임시 저장 실패: {e}") from e

    # 6. 사용자에게는 request_id + region + tags만 반환 (embedding, candidate_ids는 비공개)
    return {
        "request_id": request_id,
        "region": condition.region,
        "tags": tags,
    }
