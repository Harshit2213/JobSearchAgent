from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Primary LLM (required)
    anthropic_api_key: str

    # Job board APIs (required)
    adzuna_app_id: str
    adzuna_app_key: str
    adzuna_country: str = "us"

    # Groq — optional fallback / fast backend
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Circuit breaker
    circuit_breaker_threshold: int = 3
    circuit_breaker_timeout: float = 60.0

    max_jobs_per_source: int = 25
    max_upload_bytes: int = 5 * 1024 * 1024


settings = Settings()
