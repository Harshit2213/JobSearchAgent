from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    adzuna_app_id: str
    adzuna_app_key: str
    adzuna_country: str = "us"

    max_jobs_per_source: int = 25
    max_upload_bytes: int = 5 * 1024 * 1024  # 5 MB


settings = Settings()
