"""Centralized configuration from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    ollama_base_url: str = "http://localhost:11434"

    # Database
    database_url: str = "sqlite:///./data/excel_genius.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
