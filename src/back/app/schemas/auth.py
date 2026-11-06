from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SignupIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    password: str = Field(min_length=8, max_length=64)
    name: str = Field(min_length=1, max_length=50)
    user_type: Literal["manager", "self_employed", "freelancer"] = "manager"


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    user_type: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    user: UserOut
