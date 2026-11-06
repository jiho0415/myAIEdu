from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import (
    create_token, decode_token, hash_password, is_password_too_long, verify_password,
)
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginIn, SignupIn


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    def signup(self, data: SignupIn) -> tuple[str, User]:
        if is_password_too_long(data.password):
            raise BadRequestError("비밀번호가 너무 깁니다. 영문·숫자는 72자, 한글은 24자 이내로 입력해 주세요.")
        email = data.email.lower()
        if self.users.get_by_email(email):
            raise ConflictError("이미 가입된 이메일입니다.")
        user = self.users.add(User(email=email, password_hash=hash_password(data.password),
                                   name=data.name, user_type=data.user_type))
        self.users.commit()
        return create_token(user.id), user

    def login(self, data: LoginIn) -> tuple[str, User]:
        user = self.users.get_by_email(data.email.lower())
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("이메일 또는 비밀번호가 올바르지 않습니다.")
        return create_token(user.id), user

    def authenticate(self, token: str) -> User:
        user_id = decode_token(token)
        user = self.users.get(user_id) if user_id else None
        if not user:
            raise UnauthorizedError("인증이 만료되었습니다. 다시 로그인해 주세요.")
        return user

    @staticmethod
    def ensure_admin(user: User) -> User:
        if user.role != "admin":
            raise ForbiddenError("관리자만 사용할 수 있습니다.")
        return user
