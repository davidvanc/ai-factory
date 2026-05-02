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


# Singleton instance - importeer dit in je code
settings = ServiceSettings()
