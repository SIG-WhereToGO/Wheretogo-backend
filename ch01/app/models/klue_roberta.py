"""
KLUE-RoBERTa 기반 여행 태그 다중 레이블(Multi-label) 분류 모델 래퍼
서버 시작 시 1회만 로딩되어 재사용돰 (ch01/app/main.py lifespan에서 로딩)
"""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from ch01.app.config.settings import settings

# ==========================================
# ==========================================
from ch01.app.schemas.tags import LABEL_ORDER


class KlueRobertaTagModel:
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = None

    def load(self) -> None:
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(settings.klue_tokenizer_path)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                settings.klue_model_path
            )
            self._model.to(self._device)
            self._model.eval()
        except Exception as e:
            raise RuntimeError(f"KLUE-RoBERTa 모델 로딩 실패: {e}") from e

    def is_loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    @torch.no_grad()
    def predict_probabilities(self, text: str) -> dict:
        """
        입력 문장에 대해 각 태그(label)별 확률(0~1)을 반환
        Multi-label 분류이므로 softmax가 아닌 sigmoid를 사용
        """
        if not self.is_loaded():
            raise RuntimeError("KLUE-RoBERTa 모델이 아직 로딩되지 않았습니다.")

        try:
            inputs = self._tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=128,
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            logits = self._model(**inputs).logits
            probs = torch.sigmoid(logits).squeeze(0).cpu().tolist()
        except Exception as e:
            raise RuntimeError(f"KLUE-RoBERTa inference 실패: {e}") from e

        if isinstance(probs, float):
            probs = [probs]

        num_labels = len(probs)
        if num_labels != len(LABEL_ORDER):

            raise RuntimeError(
                f"모델 출력 라벨 수({num_labels})와 LABEL_ORDER 길이({len(LABEL_ORDER)})가 일치하지 않습니다."
            )

        return {label: prob for label, prob in zip(LABEL_ORDER, probs)}


klue_roberta_model = KlueRobertaTagModel()
