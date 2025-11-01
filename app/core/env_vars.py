from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class EnvVars(BaseSettings):
    # API Configuration
    ALLOWED_ORIGINS: str
    
    # Postgres connection string
    POSTGRES_DATABASE_URL: str

    # JWT config
    JWT_SECRET: str
    JWT_LIFETIME_SECONDS: int = 86400

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        protected_namespaces=()
        )