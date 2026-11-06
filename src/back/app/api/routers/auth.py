from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service, get_current_user
from app.models import User
from app.schemas.auth import LoginIn, SignupIn, TokenOut, UserOut
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/auth/signup", status_code=201, response_model=TokenOut)
def signup(body: SignupIn, auth: AuthService = Depends(get_auth_service)):
    token, user = auth.signup(body)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, auth: AuthService = Depends(get_auth_service)):
    token, user = auth.login(body)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/users/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
