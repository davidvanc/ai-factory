"""
Configuratie via environment variables met Pydantic validatie.
Alle config is hier gedefinieerd; geen env.getenv() in business code.
"""
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    """Standaard settings voor elke service."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Service identificatie
    service_name: str = Field(default="unnamed-service", description="Naam voor logs/metrics")
    service_version: str = Field(default="0.1.0")
    environment: Literal["dev", "staging", "prod"] = Field(default="dev")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_format: Literal["json", "console"] = Field(default="json")

    # Observability
    metrics_enabled: bool = Field(default=True)
    metrics_path: str = Field(default="/metrics")

    # Health checks
    readiness_timeout_seconds: float = Field(default=5.0)
    # Security: Bearer token auth
    auth_enabled: bool = Field(default=False, description="Vereis Bearer token voor business endpoints")
    auth_tokens: str = Field(default="", description="Comma-separated valid bearer tokens")

    # Security: CORS
    allowed_origins: str = Field(default="*", description="Comma-separated CORS origins, of '*'")

    # Security: rate limiting
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    rate_limit_redis_url: str = Field(
        default="redis://localhost:6379/1",
        description="Redis URL for rate limiting; override per deployment"
    )
    # Resilience: request limits
    max_request_body_bytes: int = Field(default=1_048_576, description="Max request body size (1MB default)")
    request_timeout_seconds: float = Field(default=30.0, ge=1.0, description="Hard timeout per request")

    # Database
    database_enabled: bool = Field(default=False, description="Enable Postgres database connection")
    database_mode: Literal["shared", "local"] = Field(default="local", description="shared=centrale DB, local=per-service")
    database_url: str = Field(
        default="postgresql://factory_admin:changeme@localhost:5432/factory_main",
        description="Async-compatible Postgres URL"
    )
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_pool_max_overflow: int = Field(default=10, ge=0, le=50)
    database_echo: bool = Field(default=False, description="Log alle SQL queries (debug)")

    @property
    def auth_tokens_set(self) -> set:
        return {t.strip() for t in self.auth_tokens.split(",") if t.strip()}

    @property
    def allowed_origins_list(self) -> list:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

# Singleton instance - importeer dit in je code
settings = ServiceSettings()
