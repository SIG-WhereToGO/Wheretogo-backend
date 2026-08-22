"""
애플리케이션 설정
POST /analyze 기능에서만 사용하는 설정을 모아둠
"""
import os, json, logging
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

from huggingface_hub import hf_hub_download
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

class Settings(BaseSettings):
    # Configure how the Pydantic settings model behaves
    #model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ==========================================
    # USER CONFIGURATION
    # 사용자가 직접 Fine-Tuning한 KLUE-RoBERTa 모델 / tokenizer 경로
    # ==========================================
    klue_model_path: str = os.getenv("KLUE_MODEL_PATH", "./ml_models/klue-roberta-travel-tag")
    klue_tokenizer_path: str = os.getenv("KLUE_TOKENIZER_PATH", "./ml_models/klue-roberta-travel-tag")
    hf_token: str = os.getenv("HF_TOKEN", "")

    #klue_model_path: str = os.getenv("KLUE_MODEL_PATH", "C:\pyCoding\SIG1\KLUE_MODEL\RoBERTaforProject\content\trained\20260805_210942")
    #klue_tokenizer_path: str = os.getenv("KLUE_TOKENIZER_PATH", "C:\pyCoding\SIG1\KLUE_MODEL\RoBERTaforProject\content\trained\20260805_210942")
    
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
    tag_threshold_default: float = float(os.getenv("DEFAULT_TAG_THRESHOLD", 0.5))
    tag_threshold_overrides: dict[str, float] = {}
    
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

    # ==========================================
    # Recommendation CONFIGURATION
    # 아래는 신규 POST /recommendaion API 에서만 사용하는 값입니다.
    # ==========================================
    tag_weight: float = float(os.getenv("TAG_WEIGHT", 0.5))
    similarity_weight: float = float(os.getenv("SIMILARITY_WEIGHT", 0.5))

    style_Tag_filter_limit: int = int(os.getenv("STYLE_TAG_FILTER_LIMIT", "300"))
    vector_filter_limit: int = int(os.getenv("VECTOR_FILTER_LIMIT", "100"))

    final_top_n: int = int(os.getenv("FINAL_TOP_N", "10"))

def _load_thresholds(settings: Settings) -> dict:
    """
    1. Hugging Face repository에서 best_threshold.json 탐색
    2. 실패하면 로컬 모델 폴더의 best_threshold.json 사용
    """

    model_path = Path(settings.klue_model_path)

    if model_path.exists():
        threshold_file = model_path / "best_threshold.json"
        
    else:
        try:
            threshold_file = hf_hub_download(
                repo_id=settings.klue_model_path,
                filename="best_threshold.json",
                token=settings.hf_token or None,
            )

        except Exception as e:
            raise FileNotFoundError(
                f"Hugging Face Repository에서 "
                f"best_threshold.json을 찾을 수 없습니다: "
                f"{settings.klue_model_path}"
            ) from e
        
    with open(threshold_file, "r", encoding="utf-8") as f:
        return json.load(f)

@lru_cache
def get_settings() -> Settings:
    
    settings = Settings()
    logger = logging.getLogger(__name__)

    try:
        settings.tag_threshold_overrides = _load_thresholds(settings)

    except Exception as e:

        logger.exception(
            "threshold 로딩 실패. 기본 threshold를 사용합니다."
        )

        settings.tag_threshold_overrides = {
            "user_input_threshold": 0.6399999999999997,
            "tourist_description_threshold": 0.6899999999999997
        }

    return settings

settings = get_settings()