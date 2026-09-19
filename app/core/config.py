"""APEX Configuration module using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "production"
    app_host: str = "0.0.0.0"
    app_port: int = 5011
    allowed_origins: str = ""

    # PostgreSQL (Read-Only access to scm_db)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "scm_db"
    postgres_user: str = "postgres"
    postgres_password: str = "password"

    # JWT Authentication (shared secret with ms-authentication)
    jwt_secret: str = "SuperSecretKeyForDevelopmentPurposesThatIsAtLeast32BytesLong!"
    jwt_issuer: str = "http://localhost:5007"
    jwt_audience: str = "http://localhost:3000"

    @property
    def postgres_connection_string(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
