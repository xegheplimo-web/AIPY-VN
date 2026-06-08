"""
Configuration validation and management.

Validates required environment variables and provides configuration access.
"""


from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore"
    )

    @field_validator("url")
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL must be set")
        if "username:password" in v:
            raise ValueError(
                "DATABASE_URL must be set with actual credentials, not placeholder 'username:password'"
            )
        return v


class RedisConfig(BaseModel):
    """Redis configuration."""

    url: str = Field(default="redis://localhost:6379/0")
    enabled: bool = Field(default=True)


class QdrantConfig(BaseModel):
    """Qdrant vector database configuration."""

    url: str = Field(default="http://localhost:6333")
    api_key: str | None = Field(default=None)
    collection: str = Field(default="vietstore_products")
    vector_size: int = Field(default=384)


class ECCConfig(BaseModel):
    """ECC cryptography configuration."""

    private_key_pem: str | None = Field(default=None, alias="ECC_PRIVATE_KEY_PEM")

    @field_validator("private_key_pem")
    def validate_ecc_key(cls, v):
        if v and not v.startswith("-----BEGIN"):
            raise ValueError("ECC_PRIVATE_KEY_PEM must be a valid PEM format")
        return v


class OllamaConfig(BaseModel):
    """Ollama cloud configuration."""

    cloud_api_key: str | None = Field(default=None, alias="OLLAMA_CLOUD_API_KEY")
    cloud_url: str = Field(default="https://api.ollama.com", alias="OLLAMA_CLOUD_URL")
    default_model: str = Field(default="qwen3.5:cloud", alias="OLLAMA_DEFAULT_MODEL")
    cloud_models: str = Field(
        default="minimax-m3:cloud,kimi-k2.6:cloud,glm-5.1:cloud,qwen3.5:cloud,nemotron-3-super:cloud,gemma4-31b-cloud",
        alias="OLLAMA_CLOUD_MODELS",
    )
    timeout: int = Field(default=30, alias="OLLAMA_TIMEOUT")

    @field_validator("cloud_api_key")
    def validate_api_key(cls, v):
        if v and not v.startswith("sk-"):
            raise ValueError("OLLAMA_CLOUD_API_KEY must start with 'sk-'")
        return v


class FirebaseConfig(BaseModel):
    """Firebase configuration for push notifications."""

    project_id: str = Field(default="", alias="FIREBASE_PROJECT_ID")
    private_key_id: str = Field(default="", alias="FIREBASE_PRIVATE_KEY_ID")
    private_key: str = Field(default="", alias="FIREBASE_PRIVATE_KEY")
    client_email: str = Field(default="", alias="FIREBASE_CLIENT_EMAIL")
    client_id: str = Field(default="", alias="FIREBASE_CLIENT_ID")
    auth_uri: str = Field(
        default="https://accounts.google.com/o/oauth2/auth", alias="FIREBASE_AUTH_URI"
    )
    token_uri: str = Field(
        default="https://oauth2.googleapis.com/token", alias="FIREBASE_TOKEN_URI"
    )
    auth_provider_x509_cert_url: str = Field(
        default="https://www.googleapis.com/oauth2/v1/certs",
        alias="FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
    )
    client_x509_cert_url: str = Field(default="", alias="FIREBASE_CLIENT_X509_CERT_URL")

    def is_configured(self) -> bool:
        """Check if Firebase is properly configured."""
        return bool(self.project_id and self.private_key and self.client_email)


class SentryConfig(BaseModel):
    """Sentry configuration for error tracking."""

    dsn: str = Field(default="", alias="SENTRY_DSN")
    environment: str = Field(default="development", alias="SENTRY_ENVIRONMENT")
    sample_rate: float = Field(default=1.0, alias="SENTRY_SAMPLE_RATE")
    traces_sample_rate: float = Field(default=0.1, alias="SENTRY_TRACES_SAMPLE_RATE")
    profiles_sample_rate: float = Field(
        default=0.1, alias="SENTRY_PROFILES_SAMPLE_RATE"
    )

    def is_configured(self) -> bool:
        """Check if Sentry is properly configured."""
        return bool(self.dsn)


class SMTPConfig(BaseModel):
    """SMTP configuration for email sending."""

    host: str = Field(default="", alias="SMTP_HOST")
    port: int = Field(default=587, alias="SMTP_PORT")
    user: str = Field(default="", alias="SMTP_USER")
    password: str = Field(default="", alias="SMTP_PASSWORD")
    from_email: str = Field(default="", alias="SMTP_FROM_EMAIL")
    use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    def is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(self.host and self.user and self.password and self.from_email)


class StripeConfig(BaseModel):
    """Stripe configuration for payment processing."""

    secret_key: str = Field(default="", alias="STRIPE_SECRET_KEY")
    publishable_key: str = Field(default="", alias="STRIPE_PUBLISHABLE_KEY")
    webhook_secret: str = Field(default="", alias="STRIPE_WEBHOOK_SECRET")
    currency: str = Field(default="vnd", alias="STRIPE_CURRENCY")

    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return bool(self.secret_key and self.publishable_key)


class SerpAPIConfig(BaseModel):
    """SerpAPI configuration for web search."""

    api_key: str = Field(default="", alias="SERPAPI_KEY")
    engine: str = Field(default="google", alias="SERPAPI_ENGINE")
    timeout: int = Field(default=10, alias="SERPAPI_TIMEOUT")

    def is_configured(self) -> bool:
        """Check if SerpAPI is properly configured."""
        return bool(self.api_key)


class OpenMapConfig(BaseModel):
    """OpenMap.vn configuration for Vietnam-specific location data."""

    api_key: str = Field(default="", alias="OPENMAP_API_KEY")
    base_url: str = Field(
        default="https://api.openmap.vn/place", alias="OPENMAP_BASE_URL"
    )
    timeout: int = Field(default=10, alias="OPENMAP_TIMEOUT")

    def is_configured(self) -> bool:
        """Check if OpenMap is properly configured."""
        return bool(self.api_key)


class AppConfig(BaseSettings):
    """Application configuration."""

    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")

    # Database
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Redis
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # Qdrant
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)

    # ECC
    ecc: ECCConfig = Field(default_factory=ECCConfig)

    # Ollama Cloud
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)

    # Firebase
    firebase: FirebaseConfig = Field(default_factory=FirebaseConfig)

    # Sentry
    sentry: SentryConfig = Field(default_factory=SentryConfig)

    # SMTP
    smtp: SMTPConfig = Field(default_factory=SMTPConfig)

    # Stripe
    stripe: StripeConfig = Field(default_factory=StripeConfig)

    # SerpAPI
    serpapi: SerpAPIConfig = Field(default_factory=SerpAPIConfig)

    # OpenMap
    openmap: OpenMapConfig = Field(default_factory=OpenMapConfig)

    # JWT
    jwt_access_expire_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:3001,http://localhost:3002",
        alias="CORS_ORIGINS",
    )

    # Rate limiting
    rate_limit_max_requests: int = Field(default=200, alias="RATE_LIMIT_MAX_REQUESTS")
    rate_limit_window_seconds: int = Field(
        default=60, alias="RATE_LIMIT_WINDOW_SECONDS"
    )

    # Logging
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    # CSRF
    csrf_secret_key: str = Field(default="", alias="CSRF_SECRET_KEY")

    model_config = {
        "env_file": [".env", "../.env"],
        "case_sensitive": False,
        "extra": "allow",
    }

    @field_validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


# Global config instance
config = AppConfig()


def validate_config() -> None:
    """
    Validate all required configuration.

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    if config.is_production:
        if not config.ecc.private_key_pem:
            raise ValueError("ECC_PRIVATE_KEY_PEM must be set in production")

        if "username:password" in config.database.url:
            raise ValueError(
                "DATABASE_URL must be set with actual credentials in production"
            )

        if not config.qdrant.api_key:
            print("WARNING: QDRANT_API_KEY not set in production")

        if not config.csrf_secret_key:
            print("WARNING: CSRF_SECRET_KEY not set in production")
