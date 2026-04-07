from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://unicab:changeme@db:5432/unicab"

    # Auth
    secret_key: str = "changeme-generate-a-real-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # AI
    anthropic_api_key: str = ""

    # Domain
    domain: str = "unicab.automica.it"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
