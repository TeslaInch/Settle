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

    # WhatsApp — Meta Cloud API
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_API_VERSION: str = "v19.0"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Environment
    ENVIRONMENT: str = "development"

    # Production frontend URL
    PRODUCTION_FRONTEND_URL: str = "https://settle.app"

    @property
    def WHATSAPP_BASE_URL(self) -> str:
        return (
            f"https://graph.facebook.com"
            f"/{self.WHATSAPP_API_VERSION}"
            f"/{self.WHATSAPP_PHONE_NUMBER_ID}"
            f"/messages"
        )


settings = Settings()
