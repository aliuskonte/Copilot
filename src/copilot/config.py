"""Единый модуль конфигурации. Читает параметры из окружения."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str
    openai_whisper_model: str = "whisper-1"
    openai_llm_model: str = "gpt-4o-mini"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    def model_post_init(self, __context: object) -> None:
        if not self.openai_api_key or self.openai_api_key == "sk-your-key-here":
            msg = "OPENAI_API_KEY must be set and valid. See .env.example"
            raise ValueError(msg)


@lru_cache
def get_settings() -> Settings:
    """Возвращает кэшированный экземпляр настроек."""
    return Settings()
