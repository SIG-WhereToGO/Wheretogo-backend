"""
KLUE-RoBERTa를 이용한 태그 추출 서비스
모델의 output(라벨 name 기준)을 DB의 Tag 테이블(tag_id, name)과 매핑
"""
from typing import Dict, List, Optional

from sqlalchemy import text as sql_text

from ch01.app.config.settings import get_settings
from ch01.app.database import engine
from ch01.app.models.klue_roberta import klue_roberta_model
from ch01.app.schemas.analyze import TagResult

_NONE_SUFFIX = "_none"

_tag_id_cache: Optional[Dict[str, int]] = None


def _load_tag_id_map() -> Dict[str, int]:
    """
    DB의 Tag 테이블에서 name -> tag_id 매핑을 가져와 캐싱
    
    """
    global _tag_id_cache
    if _tag_id_cache is not None:
        return _tag_id_cache

    try:
        with engine.connect() as connection:
            rows = connection.execute(
                sql_text('SELECT tag_id, name FROM "Tag";')
            ).mappings().all()
    except Exception as e:
        raise RuntimeError(f"태그 매핑 조회 실패 (PostgreSQL 연결 확인 필요): {e}") from e

    _tag_id_cache = {row["name"]: row["tag_id"] for row in rows}
    return _tag_id_cache


def extract_tags(input_text: str) -> List[TagResult]:
    settings = get_settings()

    probabilities = klue_roberta_model.predict_probabilities(input_text)
    tag_id_map = _load_tag_id_map()

    results: List[TagResult] = []
    for name, probability in probabilities.items():
        # none 계열 결과는 유효 태그 목록에서 제외
        if name.endswith(_NONE_SUFFIX):
            continue

        threshold = settings.get_tag_threshold(name)
        if probability < threshold:
            continue

        tag_id = tag_id_map.get(name)
        if tag_id is None:
            # DB에 아직 등록되지 않은 태그명이면 응답에서 제외 (로그로만 남김)
            continue

        results.append(
            TagResult(tag_id=tag_id, name=name, probability=round(float(probability), 4))
        )

    results.sort(key=lambda t: t.probability, reverse=True)
    return results
