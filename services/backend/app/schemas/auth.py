from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    nickname: str = Field(min_length=1, max_length=40)
    language: str = Field(min_length=1, max_length=40)


class LoginResponse(BaseModel):
    token: str


class TokenPayload(BaseModel):
    nickname: str
    language: str
    iat: int
    exp: int
