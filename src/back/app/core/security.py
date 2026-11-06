from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import ACCESS_TOKEN_HOURS, SECRET_KEY


# bcrypt는 72바이트까지만 처리하고, 5.x부터는 초과 시 예외를 던진다 (한글은 글자당 3바이트)
PASSWORD_MAX_BYTES = 72


def is_password_too_long(pw: str) -> bool:
    return len(pw.encode()) > PASSWORD_MAX_BYTES


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    # 길이 초과 비밀번호로는 가입할 수 없으므로 항상 불일치로 처리한다 (500 방지)
    if is_password_too_long(pw):
        return False
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> int | None:
    try:
        return int(jwt.decode(token, SECRET_KEY, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
