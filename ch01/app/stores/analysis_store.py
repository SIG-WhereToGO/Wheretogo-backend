"""
분석 결과 In-Memory 임시 저장소 (TTL 지원)

"""
import threading
import time
from typing import Any, Dict, Optional


class InMemoryAnalysisStore:
    def __init__(self, ttl_minutes: int = 30):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._ttl_minutes = ttl_minutes # Time To Live

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
