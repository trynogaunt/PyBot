from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import tomllib
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppEnv:
    discord_token: str
    guild_id: int
    config_path: Path
    staff_roles_ids: List[int]
    database_url: str


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_env() -> AppEnv:
    root = _project_root()
    log = logging.getLogger(__name__)
    try:
        app_env = os.getenv("APP_ENV", "dev").strip().lower()
    except Exception as e:
        log.error(f"Error reading APP_ENV environment variable: {e}")

    if app_env not in ("dev", "prod"):
        raise ValueError("APP_ENV environment variable must be 'dev' or 'prod'.")
    elif app_env == "prod":
        log.info("Running in production environment.")

    candidates = [
        root / f".env.{app_env}",
        root / ".env",
        root / "config" / f".env.{app_env}",
        root / "config" / ".env",
    ]
    override = False

    for path in candidates:
        if path.exists():
            log.info(f"Loaded environment variables from {path}")
            load_dotenv(dotenv_path=path, override=override)
        else:
            load_dotenv()

    try:
        discord_token = os.getenv("DISCORD_TOKEN").strip()
        guild_id_str = os.getenv("GUILD_ID").strip()
        config_path_str = os.getenv("CONFIG_PATH", "config.toml").strip()
        staff_roles_ids_str = os.getenv("STAFF_ROLES_IDS", "").strip()
        database_url = os.getenv("DATABASE_URL", "").strip()
    except Exception as e:
        log.error(f"Error reading environment variables: {e}")
        raise ValueError(
            "Error reading environment variables. Please check your .env files and environment settings."
        ) from e

    if not discord_token:
        log.error("DISCORD_TOKEN environment variable is missing.")
        raise ValueError("DISCORD_TOKEN environment variable is required.")
    if not guild_id_str or not guild_id_str.isdigit():
        log.error("GUILD_ID environment variable is missing or invalid.")
        raise ValueError("GUILD_ID environment variable is required and must be an integer.")
    if not config_path_str:
        log.error("CONFIG_PATH environment variable is missing.")
        raise ValueError("CONFIG_PATH environment variable is required.")
    if not staff_roles_ids_str:
        log.warning("STAFF_ROLES_IDS environment variable is missing or empty.")
        staff_roles_ids_str = ""

    guild_id = int(guild_id_str)
    config_path = Path(config_path_str)

    return AppEnv(
        discord_token=discord_token,
        guild_id=guild_id,
        config_path=config_path,
        staff_roles_ids=[int(role_id) for role_id in staff_roles_ids_str.split(",") if role_id],
        database_url=database_url,
    )


def load_config(config_path: Path) -> Dict:
    log = logging.getLogger(__name__)
    if not config_path.exists():
        log.error(f"Configuration file not found at {config_path}")
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    for key in ("enabled_features", "features"):
        if key not in data:
            log.error(f"Missing required configuration key: {key}")
            raise KeyError(f"Missing required configuration key: {key}")

    if not isinstance(data["enabled_features"], list):
        log.error("enabled_features must be a list.")
        raise TypeError("enabled_features must be a list.")
    if not isinstance(data["features"], dict):
        log.error("features must be a dictionary.")
        raise TypeError("features must be a dictionary.")

    return data
