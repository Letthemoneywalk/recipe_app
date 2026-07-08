from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 дней
    ANTHROPIC_API_KEY: str
    SPOONACULAR_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()