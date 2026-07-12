from pydantic import BaseModel, EmailStr
from models.user import UserDiet
from pydantic import BaseModel, EmailStr, field_validator

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен быть не менее 6 символов')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    name: str | None = None
    age: int | None = None
    weight: float | None = None
    height: float | None = None
    diet: UserDiet = UserDiet.regular
    allergens: list[str] = []


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    diet: UserDiet
    allergens: list[str] = []

    @field_validator('allergens', mode='before')
    @classmethod
    def allergens_default(cls, v):
        return v or []

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"