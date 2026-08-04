from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _float(name: str, default: float = 0.0) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class ModelConfig:
    key: str
    name: str
    base_url: str
    api_key: str
    price_input_per_1k: float
    price_output_per_1k: float

    @property
    def enabled(self) -> bool:
        return bool(self.name and self.base_url and self.api_key)


@dataclass(frozen=True)
class AppConfig:
    mock_mode: bool
    source_lang: str
    target_lang: str
    model_a: ModelConfig
    model_b: ModelConfig
    tesseract_cmd: str


def load_config() -> AppConfig:
    model_a = ModelConfig(
        key="model_a",
        name=os.getenv("MODEL_A_NAME", "gpt-4o-mini"),
        base_url=os.getenv("MODEL_A_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("MODEL_A_API_KEY", ""),
        price_input_per_1k=_float("MODEL_A_PRICE_INPUT_PER_1K", 0.00015),
        price_output_per_1k=_float("MODEL_A_PRICE_OUTPUT_PER_1K", 0.00060),
    )
    model_b = ModelConfig(
        key="model_b",
        name=os.getenv("MODEL_B_NAME", "gpt-4.1-mini"),
        base_url=os.getenv("MODEL_B_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("MODEL_B_API_KEY", ""),
        price_input_per_1k=_float("MODEL_B_PRICE_INPUT_PER_1K", 0.00040),
        price_output_per_1k=_float("MODEL_B_PRICE_OUTPUT_PER_1K", 0.00160),
    )
    return AppConfig(
        mock_mode=_bool("MOCK_MODE", True),
        source_lang=os.getenv("DEFAULT_SOURCE_LANG", "English"),
        target_lang=os.getenv("DEFAULT_TARGET_LANG", "Chinese"),
        model_a=model_a,
        model_b=model_b,
        tesseract_cmd=os.getenv("TESSERACT_CMD", ""),
    )
