from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConfigManager:
    """Central place for paths and runtime settings."""

    project_root: Path = Path(__file__).resolve().parent.parent
    database_name: str = "tech_trends.db"
    request_timeout: int = 10
    max_workers: int = 5
    user_agent: str = "TechTrendStudentBot/1.0"
    trending_url: str = "https://github.com/trending"

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def database_path(self) -> Path:
        return self.data_dir / self.database_name

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
