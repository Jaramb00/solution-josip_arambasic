from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TICKETHUB_", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./tickethub.db"

    dummyjson_base_url: str = "https://dummyjson.com"
    http_timeout: float = 20.0

    # Pri pokretanju automatski napuni bazu iz vanjskog izvora ako je prazna.
    sync_on_startup: bool = True


settings = Settings()
