import os

from dotenv import load_dotenv
from sqlalchemy import create_engine


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL이 설정되지 않았습니다.")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)