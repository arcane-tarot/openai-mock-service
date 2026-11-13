from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

MockScenario = Literal[
    "success",
    "unauthorized",
    "rate_limit",
    "server_error",
    "empty",
    "timeout",
]


class Settings(BaseSettings):
    mock_api_key: str = "sk-mock-local"
    mock_scenario: MockScenario = "success"
    mock_delay_ms: int = Field(default=0, ge=0, le=60_000)
    mock_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    allow_scenario_header: bool = False
    log_prompts: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
