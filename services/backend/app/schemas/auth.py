from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    token: str


class RegisterRequest(BaseModel):
    username: EmailStr
    password: str = Field(min_length=8)
    nickname: str = Field(min_length=1, max_length=40)
    language: str = Field(min_length=1, max_length=40)

    @field_validator("username")
    @classmethod
    def username_must_use_deploy_domain(cls, username: EmailStr) -> str:
        normalized_username = str(username).lower()

        if not normalized_username.endswith("@deploy.co"):
            raise ValueError("username_must_be_deploy_email")

        return normalized_username


class RegisterResponse(BaseModel):
    username: str


class TokenPayload(BaseModel):
    nickname: str
    language: str
    iat: int
    exp: int
