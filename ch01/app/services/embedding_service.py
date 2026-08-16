"""
SBERT를 이용한 입력문 embedding 생성 서비스

"""
from typing import List

from ch01.app.models.sbert import sbert_model


def generate_embedding(input_text: str) -> List[float]:
    return sbert_model.encode(input_text)
