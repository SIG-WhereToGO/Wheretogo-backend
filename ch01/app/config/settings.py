"""
애플리케이션 설정
POST /analyze 기능에서만 사용하는 설정을 모아둠
"""
import os
from functools import lru_cache
from typing import Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ==========================================
    # USER CONFIGURATION
    # 사용자가 직접 Fine-Tuning한 KLUE-RoBERTa 모델 / tokenizer 경로
    # ==========================================
    klue_model_path: str = os.getenv("KLUE_MODEL_PATH", "./ml_models/klue-roberta-travel-tag")
    klue_tokenizer_path: str = os.getenv("KLUE_TOKENIZER_PATH", "./ml_models/klue-roberta-travel-tag")

    # ==========================================
    # USER CONFIGURATION
    # 준비된 SBERT 모델 경로
    # ==========================================
    sbert_model_path: str = os.getenv("SBERT_MODEL_PATH", "./ml_models/sbert-travel")

    # ==========================================
    # USER CONFIGURATION
    # 지역/거리 조건 추출용 LLM API 접속 정보
    # ==========================================
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_api_base_url: str = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1")
    llm_model_name: str = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

    # ==========================================
    # USER CONFIGURATION
    # 태그 threshold (기본값). Fine-Tuning 시 태그별로 다른 threshold를 정했다면
    # tag_threshold_overrides 에 {"태그명": threshold} 형태로 채우기
    # 예: {"style_activity": 0.45, "companion_pet": 0.6}
    # ==========================================
    tag_threshold_default: float = float(os.getenv("TAG_THRESHOLD", "0.5"))
    tag_threshold_overrides: Dict[str, float] = {}

    # ==========================================
    # USER CONFIGURATION
    # "주변", "근처" 등 표현은 있지만 구체적인 거리가 없을 때 사용할 기본 반경(km)
    # ==========================================
    default_radius_km: float = float(os.getenv("DEFAULT_RADIUS_KM", "3"))

    # ==========================================
    # USER CONFIGURATION
    # In-Memory Store TTL(분). 이 시간이 지나면 분석 결과가 자동 삭제
    # ==========================================
    analysis_ttl_minutes: int = int(os.getenv("ANALYSIS_TTL_MINUTES", "30"))

    # ==========================================
    # USER CONFIGURATION
    # PostGIS 사용 여부.
    # true  -> ST_DWithin 기반 거리 필터링 (DB에 PostGIS extension 및 geography 계산 가능해야 함)
    # false -> Haversine Formula 기반 거리 필터링 (애플리케이션 레벨 계산)
    # ==========================================
    use_postgis: bool = os.getenv("USE_POSTGIS", "false").lower() == "true"

    # 입력문 길이 제한 (너무 긴 입력 방지)
    max_input_length: int = int(os.getenv("MAX_INPUT_LENGTH", "300"))

    def get_tag_threshold(self, tag_name: str) -> float:
        return self.tag_threshold_overrides.get(tag_name, self.tag_threshold_default)


@lru_cache
def get_settings() -> Settings:
    return Settings()
