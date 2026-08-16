"""
pytest 실행 전 필요한 환경변수를 세팅합니다.
ch01/app/database.py는 모듈 import 시점에 DATABASE_URL이 반드시 설정되어 있어야 하므로
(기존 코드 로직, 수정하지 않음) 테스트에서는 더미 값을 채워줍니다.
실제 DB에 연결하지는 않으며, test_analyze_api.py에서는 lifespan(DB 연결/모델 로딩)을
직접 실행하지 않는 방식으로 테스트합니다.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost:5432/dummy")
os.environ.setdefault("LLM_API_KEY", "dummy-key-for-tests")
