"""
LLM API를 이용한 지역 및 거리 조건 추출 서비스
LLM은 절대 여행지를 직접 추천하지 않고, 아래 구조만 추출

{ "region": str | None, "nearby": bool, "distance": float | None, "unit": str | None }
"""
import json
import re
from typing import Optional

import httpx
from pydantic import BaseModel

from ch01.app.config.settings import settings


class RegionCondition(BaseModel):
    region: Optional[str] = None
    nearby: bool = False
    distance: Optional[float] = None
    unit: Optional[str] = None


_SYSTEM_PROMPT = """당신은 여행 요청 문장에서 지역 및 거리 조건만 추출하는 파서입니다.
여행지를 추천하지 마세요. 오직 아래 JSON 형식으로만 응답하고, 다른 설명은 절대 포함하지 마세요.

{"region": string|null, "nearby": boolean, "distance": number|null, "unit": string|null}

규칙:
- region: 문장에 등장하는 지역/장소명 (예: "부산", "해운대", "부산역"). 없으면 null.
  - 한국에는 이름이 겹치는 서로 다른 지역이 있습니다 (예: "광주"는 광주광역시와
    경기도 광주시 둘 다 될 수 있고, "고성"은 강원도와 경상남도에 둘 다 있습니다).
    문장에 "경기도 광주", "강원도 고성"처럼 시/도 등 상위 행정구역이 함께
    언급되어 있다면, 생략하지 말고 그대로 살려서 추출하세요
    (예: 입력 "경기도 광주 쪽 여행지 추천해줘" → region: "경기도 광주").
  - 문장에 상위 행정구역 언급이 전혀 없으면 지금처럼 지역/장소명만 추출하세요
    (예: 입력 "광주 여행지 추천해줘" → region: "광주"). 문맥에 없는 상위
    행정구역을 임의로 추측해서 채우지 마세요.
- nearby: "주변", "근처", "인근" 등의 표현이 있으면 true, 없으면 false.
- distance: "3km 이내"처럼 구체적인 숫자가 있으면 그 숫자, 없으면 null.
- unit: distance의 단위("km", "m" 등). distance가 null이면 unit도 null.
"""


def _call_llm_api(input_text: str) -> str:

    if not settings.llm_api_key:
        raise RuntimeError("LLM API 호출 실패: LLM_API_KEY가 설정되지 않았습니다.")

    url = f"{settings.llm_api_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.llm_model_name,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": input_text},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=15.0)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise RuntimeError(f"LLM API 호출 실패: {e}") from e

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"LLM API 응답 형식이 올바르지 않습니다: {e}") from e


def _parse_llm_response(raw_content: str) -> RegionCondition:
    cleaned = raw_content.strip()
    cleaned = re.sub(r"^```(json)?|```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"지역 추출 실패 (LLM 응답 JSON 파싱 실패): {e}") from e

    try:
        return RegionCondition(**parsed)
    except Exception as e:
        raise RuntimeError(f"지역 추출 실패 (LLM 응답 형식 오류): {e}") from e


def extract_region_condition(input_text: str) -> RegionCondition:

    raw_content = _call_llm_api(input_text)
    condition = _parse_llm_response(raw_content)

    # "주변/근처" 표현은 있지만 구체적인 거리가 없는 경우 기본 반경 적용
    if condition.nearby and condition.distance is None:
        condition.distance = settings.default_radius_km
        condition.unit = "km"

    return condition
