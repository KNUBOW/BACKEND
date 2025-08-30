from pydantic_settings import BaseSettings
from pydantic import SecretStr
from typing import Literal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):

    JWT_SECRET_KEY: SecretStr
    SESSION_MIDDLEWARE_SECRET_KEY: SecretStr
    PHONE_PEPPER: SecretStr

    POSTGRES_DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0

    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: SecretStr
    NAVER_REDIRECT_URI: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: SecretStr
    GOOGLE_REDIRECT_URI: str

    KAKAO_CLIENT_ID: str
    KAKAO_CLIENT_SECRET: SecretStr
    KAKAO_REDIRECT_URI: str

    OLLAMA_URL: str
    MODEL_NAME: str

    ENV: Literal["dev", "prod", "test"] = "dev"

    class Config:
        env_file = str(ENV_PATH)
        case_sensitive = True


settings = Settings()  # 유효성 체크
