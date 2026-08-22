"""
SBERT embedding 모델 래퍼.
서버 시작 시 1회만 로딩되어 재사용됩니다. (ch01/app/main.py lifespan에서 로딩)
새로운 모델을 학습하지 않고, 이미 준비된 모델 파일을 그대로 로딩
"""
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from ch01.app.config.settings import settings


class SbertEmbeddingModel:
    def __init__(self):
        self._model: Optional[SentenceTransformer] = None

    def load(self) -> None:
        try:
            # SentenceTransformer는 내부적으로 CUDA 사용 가능 여부를 자동 감지하여
            # GPU가 있으면 GPU를, 없으면 CPU를 사용한다 허거덩
            self._model = SentenceTransformer(settings.sbert_model_path)
        except Exception as e:
            raise RuntimeError(f"SBERT 모델 로딩 실패: {e}") from e

    def is_loaded(self) -> bool:
        return self._model is not None

    def encode(self, text: str) -> List[float]:
        if not self.is_loaded():
            raise RuntimeError("SBERT 모델이 아직 로딩되지 않았습니다.")
        try:
            embedding = self._model.encode(text, convert_to_numpy=True)
        except Exception as e:
            raise RuntimeError(f"SBERT inference 실패: {e}") from e
        return embedding.tolist()


sbert_model = SbertEmbeddingModel()
