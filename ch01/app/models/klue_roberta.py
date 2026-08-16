"""
KLUE-RoBERTa 기반 여행 태그 다중 레이블(Multi-label) 분류 모델 래퍼
서버 시작 시 1회만 로딩되어 재사용됩니다. (ch01/app/main.py lifespan에서 로딩)
"""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from ch01.app.config.settings import get_settings

# ==========================================
# USER CONFIGURATION
# Fine-Tuning 시 사용한 라벨 순서(모델 output index 순서)를 정확히 채워주세요.
# 이 리스트의 순서는 반드시 Fine-Tuning 코드의 label2id / id2label 순서와 동일해야 합니다.
# 모델의 내부 output index를 그대로 비즈니스 로직에 사용하지 않기 위해,
# 여기서 index -> 태그 name 으로 먼저 변환한 뒤 tag_service에서 DB의 tag_id와 매핑합니다.
#
# "none" 계열 라벨(예: companion_none, style_none)이 모델 출력에 포함되어 있다면
# 이름 끝에 "_none"을 붙여 그대로 리스트에 포함해주세요. (tag_service에서 자동으로 제외됩니다)
# ==========================================
LABEL_ORDER = [
    "companion_solo",
    "companion_friend",
    "companion_romantic_partner",
    "companion_family",
    "companion_group",
    "companion_pet",
    "style_healing",
    "style_nature",
    "style_activity",
    "style_culture",
    "style_history",
    "style_photo_spot",
    "style_outdoor",
    "style_indoor",
    "style_experience",
    "style_food",
    "style_shopping",
]


class KlueRobertaTagModel:
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = None

    def load(self) -> None:
        settings = get_settings()
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
        입력 문장에 대해 각 태그(label)별 확률(0~1)을 반환합니다.
        Multi-label 분류이므로 softmax가 아닌 sigmoid를 사용합니다.
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
            # ==========================================
            # USER CONFIGURATION 확인 필요
            # 모델의 출력 라벨 개수와 LABEL_ORDER 길이가 다릅니다.
            # Fine-Tuning 시 사용한 라벨 순서(및 "none" 라벨 포함 여부)를 다시 확인해주세요.
            # ==========================================
            raise RuntimeError(
                f"모델 출력 라벨 수({num_labels})와 LABEL_ORDER 길이({len(LABEL_ORDER)})가 일치하지 않습니다."
            )

        return {label: prob for label, prob in zip(LABEL_ORDER, probs)}


klue_roberta_model = KlueRobertaTagModel()
