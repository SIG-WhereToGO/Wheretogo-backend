"""
POST /analyze API 테스트

무거운 실제 모델(KLUE-RoBERTa, SBERT) 로딩과 실제 LLM/DB 호출 없이
analyze_service.analyze()를 monkeypatch하여 라우터/스키마 레벨의 동작을 검증합니다.
(TestClient를 "with" 블록 없이 사용하여 lifespan의 모델 로딩/DB 연결을 실행하지 않습니다)

실행 방법 (레포 루트 기준):
    pytest ch01/tests/test_analyze_api.py -v
"""
from fastapi.testclient import TestClient

from ch01.app.main import app
from ch01.app.routers import analyze as analyze_router
from ch01.app.schemas.analyze import TagResult

client = TestClient(app)


def _fake_analyze(input_text: str) -> dict:
    return {
        "request_id": "9b1deb4d-3b7d-4bad-9b13-fake000001",
        "region": "부산",
        "tags": [
            TagResult(tag_id=2, name="companion_friend", probability=0.94),
            TagResult(tag_id=10, name="style_activity", probability=0.91),
        ],
    }


def test_analyze_success(monkeypatch):
    monkeypatch.setattr(analyze_router, "analyze", _fake_analyze)

    response = client.post(
        "/analyze",
        json={"input_text": "부산에서 친구들과 함께하기 좋은 액티비티를 추천해줘"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["region"] == "부산"
    assert body["request_id"]
    assert {tag["name"] for tag in body["tags"]} == {"companion_friend", "style_activity"}


def test_analyze_rejects_empty_input():
    response = client.post("/analyze", json={"input_text": "   "})
    assert response.status_code == 422


def test_analyze_rejects_too_long_input():
    from ch01.app.config.settings import get_settings

    settings = get_settings()
    too_long_text = "가" * (settings.max_input_length + 1)

    response = client.post("/analyze", json={"input_text": too_long_text})
    assert response.status_code == 422


def test_analyze_runtime_error_maps_to_expected_status(monkeypatch):
    def fake_analyze_llm_failure(input_text: str) -> dict:
        raise RuntimeError("LLM API 호출 실패: timeout")

    monkeypatch.setattr(analyze_router, "analyze", fake_analyze_llm_failure)

    response = client.post("/analyze", json={"input_text": "부산 여행지 추천해줘"})
    assert response.status_code == 502
