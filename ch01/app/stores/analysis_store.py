"""
분석 결과 In-Memory 임시 저장소 (TTL 지원)
==========================================
USER CONFIGURATION
현재는 단일 서버 환경을 가정한 In-Memory 저장 방식입니다.
서버가 여러 대로 확장되거나 재시작 시에도 데이터를 유지해야 한다면,
이 클래스와 동일한 인터페이스(set/get/cleanup_expired)를 갖는
Redis 기반 구현체로 교체해주세요. (analyze_service.py 등 사용하는 쪽 코드는 수정할 필요 없음)
==========================================
"""
import threading
import time
from typing import Any, Dict, Optional


class InMemoryAnalysisStore:
    def __init__(self, ttl_minutes: int = 30):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._ttl_minutes = ttl_minutes

    def set(self, request_id: str, value: Dict[str, Any]) -> None:
        expires_at = time.time() + self._ttl_minutes * 60
        with self._lock:
            self._store[request_id] = {"value": value, "expires_at": expires_at}

    def get(self, request_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._store.get(request_id)
            if entry is None:
                return None
            if entry["expires_at"] < time.time():
                del self._store[request_id]
                return None
            return entry["value"]

    def set_ttl_minutes(self, ttl_minutes: int) -> None:
        self._ttl_minutes = ttl_minutes

    def cleanup_expired(self) -> None:
        now = time.time()
        with self._lock:
            expired_keys = [k for k, v in self._store.items() if v["expires_at"] < now]
            for key in expired_keys:
                del self._store[key]


# 실제 TTL 값은 main.py의 lifespan에서 settings.analysis_ttl_minutes로 주입됩니다.
analysis_store = InMemoryAnalysisStore()
