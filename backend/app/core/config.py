from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="PulseTrace", alias="APP_NAME")
    app_env: Literal["development", "test", "staging", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+psycopg://pulsetrace:change_me@localhost:5433/pulsetrace",
        alias="DATABASE_URL",
    )
    cors_origins_env: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="BACKEND_CORS_ORIGINS",
    )
    jwt_secret_key: str = Field(
        default="dev-only-change-me-use-openssl-rand-hex-32",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    auth_cookie_name: str = Field(default="pulsetrace_access_token", alias="AUTH_COOKIE_NAME")
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax",
        alias="AUTH_COOKIE_SAMESITE",
    )
    log_upload_max_bytes: int = Field(
        default=10 * 1024 * 1024,
        alias="LOG_UPLOAD_MAX_BYTES",
    )
    log_storage_path: str = Field(
        default="../data/uploads",
        alias="LOG_STORAGE_PATH",
    )
    log_insert_batch_size: int = Field(default=500, alias="LOG_INSERT_BATCH_SIZE")
    log_error_summary_max_chars: int = Field(
        default=4000,
        alias="LOG_ERROR_SUMMARY_MAX_CHARS",
    )
    analysis_window_hours: int = Field(default=24, alias="ANALYSIS_WINDOW_HOURS")
    analysis_bucket_minutes: int = Field(default=60, alias="ANALYSIS_BUCKET_MINUTES")
    analysis_min_samples: int = Field(default=5, alias="ANALYSIS_MIN_SAMPLES")
    analysis_zscore_threshold: float = Field(default=2.5, alias="ANALYSIS_ZSCORE_THRESHOLD")
    analysis_if_contamination: float = Field(default=0.1, alias="ANALYSIS_IF_CONTAMINATION")
    analysis_if_min_rows: int = Field(default=8, alias="ANALYSIS_IF_MIN_ROWS")
    analysis_max_logs: int = Field(default=20000, alias="ANALYSIS_MAX_LOGS")
    cluster_max_logs: int = Field(default=5000, alias="CLUSTER_MAX_LOGS")
    cluster_dbscan_eps: float = Field(default=0.35, alias="CLUSTER_DBSCAN_EPS")
    cluster_min_samples: int = Field(default=3, alias="CLUSTER_MIN_SAMPLES")
    cluster_max_clusters: int = Field(default=50, alias="CLUSTER_MAX_CLUSTERS")
    analysis_random_seed: int = Field(default=42, alias="ANALYSIS_RANDOM_SEED")
    incident_correlation_lookback_hours: int = Field(
        default=72,
        alias="INCIDENT_CORRELATION_LOOKBACK_HOURS",
    )
    incident_correlation_window_minutes: int = Field(
        default=90,
        alias="INCIDENT_CORRELATION_WINDOW_MINUTES",
    )
    incident_deployment_window_minutes: int = Field(
        default=120,
        alias="INCIDENT_DEPLOYMENT_WINDOW_MINUTES",
    )
    rca_lookback_hours: int = Field(default=48, alias="RCA_LOOKBACK_HOURS")
    rca_max_logs: int = Field(default=200, alias="RCA_MAX_LOGS")
    rca_deployment_window_minutes: int = Field(default=180, alias="RCA_DEPLOYMENT_WINDOW_MINUTES")
    rca_weight_temporal: float = Field(default=12.0, alias="RCA_WEIGHT_TEMPORAL")
    rca_weight_deployment: float = Field(default=18.0, alias="RCA_WEIGHT_DEPLOYMENT")
    rca_weight_service: float = Field(default=20.0, alias="RCA_WEIGHT_SERVICE")
    rca_weight_dependency: float = Field(default=16.0, alias="RCA_WEIGHT_DEPENDENCY")
    rca_weight_error_pattern: float = Field(default=14.0, alias="RCA_WEIGHT_ERROR_PATTERN")
    rca_weight_traffic: float = Field(default=10.0, alias="RCA_WEIGHT_TRAFFIC")
    rca_weight_severity: float = Field(default=10.0, alias="RCA_WEIGHT_SEVERITY")
    rca_contradiction_penalty: float = Field(default=15.0, alias="RCA_CONTRADICTION_PENALTY")
    rca_ollama_enabled: bool = Field(default=False, alias="RCA_OLLAMA_ENABLED")
    rca_ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="RCA_OLLAMA_BASE_URL")
    rca_ollama_model: str = Field(default="llama3.2", alias="RCA_OLLAMA_MODEL")
    rate_limit_auth_per_minute: int = Field(default=20, alias="RATE_LIMIT_AUTH_PER_MINUTE")
    rate_limit_expensive_per_minute: int = Field(default=10, alias="RATE_LIMIT_EXPENSIVE_PER_MINUTE")
    log_storage_backend: Literal["filesystem", "s3"] = Field(
        default="filesystem",
        alias="LOG_STORAGE_BACKEND",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def backend_cors_origins(self) -> list[str]:
        return _parse_csv_list(self.cors_origins_env)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()