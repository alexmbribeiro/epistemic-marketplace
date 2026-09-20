from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://epistemic:epistemic_secret@localhost:5432/epistemic"
    redis_url: str = "redis://localhost:6379"
    anthropic_api_key: str = ""
    secret_key: str = "supersecretkey_change_in_production"
    access_token_expire_minutes: int = 60

    # Prefixed AGENT_* rather than CLAUDE_*: a shell running inside Claude Code
    # already exports CLAUDE_EFFORT, which would silently override this.
    agent_model: str = "claude-sonnet-5"
    # Thinking counts against max_tokens, so this needs headroom above the
    # structured output itself (~800 tokens) or the tool_use block truncates.
    agent_max_tokens: int = 4096
    # Sonnet 5 defaults to "high"; "low" keeps a debate's 18 calls affordable.
    agent_effort: str = "low"

    # Comma-separated. The deployed frontend origin must be listed here.
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
