"""Settings from environment variables (prefix ``DF_``) and an optional ``.env`` file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DF_", env_file=".env", extra="ignore")

    data_dir: Path = Path("data")
    datasets_dir: Path = Path("datasets")


@lru_cache
def get_settings() -> Settings:
    return Settings()
