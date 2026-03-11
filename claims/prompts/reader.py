from __future__ import annotations
from datetime import date
from pathlib import Path
from threading import RLock
from typing import Dict, Any, Optional


def _default_variables() -> Dict[str, Any]:
    """Variables that are always injected dynamically (never cached)."""
    return {
        "__today__": date.today().isoformat(),
    }


class PromptReader:

    _lock: RLock = RLock()
    _cache: Dict[str, str] = {}  # Stores raw template text only

    @classmethod
    def _prompts_dir(cls) -> Path:
        return Path(__file__).resolve().parent

    @classmethod
    def get(
        cls,
        filename: str,
        *,
        variables: Optional[Dict[str, Any]] = None,
        force_reload: bool = False,
    ) -> str:
        if not filename or not isinstance(filename, str):
            raise ValueError("Prompt filename must be a non-empty string.")

        key = filename.strip().replace("\\", "/")

        with cls._lock:
            if force_reload or key not in cls._cache:
                prompt_path = cls._prompts_dir() / key
                if not prompt_path.exists():
                    raise FileNotFoundError(f"Prompt not found: {prompt_path}")

                text = prompt_path.read_text(encoding="utf-8").strip()
                if not text:
                    raise ValueError(f"Prompt file is empty: {prompt_path}")

                cls._cache[key] = text  # Cache raw template only

            raw_template = cls._cache[key]

        # Always resolve dynamic variables fresh (never cached)
        merged = _default_variables()
        if variables:
            merged.update(variables)

        return cls._render(raw_template, merged)

    @classmethod
    def _render(cls, template: str, variables: Dict[str, Any]) -> str:
        """Replace {{key}} placeholders with variable values."""
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

    @classmethod
    def clear_cache(cls) -> None:
        with cls._lock:
            cls._cache.clear()