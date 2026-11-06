import os
from pathlib import Path

# src/back 디렉토리 (실행 위치(CWD)와 무관하게 DB 경로를 고정)
BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'myaiedu.db').as_posix()}")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me-please-0123456789abcdef")
ACCESS_TOKEN_HOURS = 24
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
).split(",")
# 개발용 관리자 계정 (운영에서는 반드시 환경변수로 교체)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@myaiedu.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")
