from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://epistemic:epistemic_secret@localhost:5432/epistemic"
    redis_url: str = "redis://localhost:6379"
    anthropic_api_key: str = ""
    secret_key: str = "supersecretkey_change_in_production"
    access_token_expire_minutes: int = 60
    claude_model: str = "claude-sonnet-4-6"

    class Config:
        env_file = ".env"


settings = Settings()
