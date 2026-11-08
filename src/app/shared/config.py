from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_base_dir() -> Path:
    return Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Configurações globais da aplicação ClickOn."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    base_dir: Path = Field(default_factory=_default_base_dir)
    default_excel_filename: str = "codigo.xlsx"
    default_delay_seconds: float = 1.5
    default_countdown_seconds: int = 4
    always_on_top: bool = True

    @property
    def default_excel_path(self) -> Path:
        return self.base_dir / self.default_excel_filename


@lru_cache
def get_settings() -> Settings:
    return Settings()
