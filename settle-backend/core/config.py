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
    SUPABASE_ANON_KEY: str

    # Termii (SMS/OTP)
    TERMII_API_KEY: str
    TERMII_SENDER_ID: str

    # WhatsApp (360Dialog)
    WHATSAPP_API_KEY: str
    WHATSAPP_URL: str = "https://waba.360dialog.io/v1"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Environment
    ENVIRONMENT: str = "development"

    # Production frontend URL (placeholder for now)
    PRODUCTION_FRONTEND_URL: str = "https://settle.app"


settings = Settings()
