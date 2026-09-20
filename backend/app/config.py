from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://epistemic:epistemic_secret@localhost:5432/epistemic"
    redis_url: str = "redis://localhost:6379"
    gemini_api_key: str = ""
    secret_key: str = "supersecretkey_change_in_production"
    access_token_expire_minutes: int = 60

    # gemini-3.8-flash is on the free tier, which is what makes an 18-call
    # debate free to run.
    agent_model: str = "gemini-3.8-flash"
    # Thinking counts against the output budget, so this needs headroom above
    # the structured output itself (~800 tokens) or the JSON comes back cut off.
    agent_max_tokens: int = 4096
    # minimal | low | medium | high
    agent_thinking_level: str = "low"
    agent_max_retries: int = 4

    # Comma-separated. The deployed frontend origin must be listed here.
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # extra="ignore" so a leftover key in .env (an old ANTHROPIC_API_KEY, say)
    # does not crash startup — and never gets echoed into a validation error.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
