from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # Email — Resend
    RESEND_API_KEY: str
    FROM_EMAIL: str = "agreements@settle.app"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # URLs
    FRONTEND_URL: str

    # Environment
    ENVIRONMENT: str = "development"


settings = Settings()
