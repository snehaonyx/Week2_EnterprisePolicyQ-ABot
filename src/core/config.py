"""Centralized environment configuration.

Every tunable the app needs is read here, once, instead of scattering
os.getenv() calls across modules.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CHROMA_PERSIST_DIR = "./data/chroma"


@dataclass(frozen=True)
class Config:
    chroma_persist_dir: str
    # No default: the correct value must be verified against Google's
    # current model list at implementation time (see docs/architecture.md
    # §5) rather than guessed here. None if CHAT_MODEL_NAME is unset.
    chat_model_name: str | None


def get_config() -> Config:
    return Config(
        chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", DEFAULT_CHROMA_PERSIST_DIR),
        chat_model_name=os.getenv("CHAT_MODEL_NAME") or None,
    )
