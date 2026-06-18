from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


CONFIG_PATH = Path("config") / "candidate.json"
APP_DIRS = [
    Path("parser"),
    Path("emailer"),
    Path("ai"),
    Path("database"),
    Path("templates"),
    Path("uploads"),
    Path("logs"),
    Path("config"),
]


@dataclass
class SMTPSettings:
    host: str
    port: int
    username: str
    password: str

    @property
    def is_complete(self) -> bool:
        return bool(self.host and self.port and self.username and self.password)


def load_env() -> None:
    load_dotenv()


def _streamlit_secret(name: str) -> Any:
    try:
        import streamlit as st

        return st.secrets.get(name)
    except Exception:
        return None


def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    secret = _streamlit_secret(name)
    if secret is None:
        return default
    return str(secret)


def get_smtp_settings() -> SMTPSettings:
    port = int(_setting("SMTP_PORT", "587") or 587)
    return SMTPSettings(
        host=_setting("SMTP_HOST"),
        port=port,
        username=_setting("SMTP_USERNAME"),
        password=_setting("SMTP_PASSWORD"),
    )


def load_candidate_config() -> dict:
    if not CONFIG_PATH.exists():
        return {
            "full_name": "",
            "phone_number": "",
            "email": "",
            "linkedin": "",
            "github": "",
            "portfolio": "",
            "skills": "",
            "experience_summary": "",
            "use_openai": False,
            "max_emails_per_hour": 25,
        }
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_candidate_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
