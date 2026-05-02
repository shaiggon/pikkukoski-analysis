from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    database_path: Path
    output_dir: Path
    timezone: ZoneInfo
    models_dir: Path


def get_settings() -> Settings:
    project_root = Path(os.getenv("PIKKUKOSKI_PROJECT_ROOT", Path(__file__).resolve().parent.parent))
    data_dir = Path(os.getenv("PIKKUKOSKI_DATA_DIR", project_root / "data"))
    output_dir = Path(os.getenv("PIKKUKOSKI_OUTPUT_DIR", project_root / "generated"))
    database_path = Path(os.getenv("PIKKUKOSKI_DB_PATH", project_root / "var" / "pikkukoski.db"))
    timezone = ZoneInfo(os.getenv("PIKKUKOSKI_TIMEZONE", "Europe/Helsinki"))
    models_dir = output_dir / "models"
    return Settings(
        project_root=project_root,
        data_dir=data_dir,
        database_path=database_path,
        output_dir=output_dir,
        timezone=timezone,
        models_dir=models_dir,
    )


def ensure_directories(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.models_dir.mkdir(parents=True, exist_ok=True)

