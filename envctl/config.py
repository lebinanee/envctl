"""Configuration management for envctl profiles."""

import os
import json
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG_DIR = Path.home() / ".envctl"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

VALID_ENVS = {"local", "staging", "production"}


class Config:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self._data = self._load()

    def _load(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return json.load(f)
        return {"profiles": {}, "active_env": "local"}

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get_active_env(self) -> str:
        return self._data.get("active_env", "local")

    def set_active_env(self, env: str):
        if env not in VALID_ENVS:
            raise ValueError(f"Invalid environment '{env}'. Choose from: {', '.join(VALID_ENVS)}")
        self._data["active_env"] = env
        self.save()

    def get_profile(self, env: str) -> dict:
        return self._data["profiles"].get(env, {})

    def set_profile(self, env: str, variables: dict):
        self._data["profiles"][env] = variables
        self.save()

    def list_envs(self) -> list:
        return list(self._data["profiles"].keys())
