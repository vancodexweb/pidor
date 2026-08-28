from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    main_bot_token: str

    postgres_user: str = "bot"
    postgres_password: str = "bot"
    postgres_db: str = "bot"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    encryption_key: str

    log_level: str = "INFO"
    default_timezone: str = "Europe/Moscow"

    @cached_property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def get_settings() -> Settings:
    return Settings()
