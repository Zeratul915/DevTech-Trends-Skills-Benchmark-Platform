from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .models import RepoItem, SkillItem, TrendSnapshot


class DBManager:
    """Owns all SQLite persistence details."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with closing(self.connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS repos (
                    name TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    description TEXT,
                    language TEXT,
                    stars INTEGER
                );

                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_name TEXT NOT NULL,
                    skill_name TEXT NOT NULL,
                    source_text TEXT,
                    FOREIGN KEY(repo_name) REFERENCES repos(name)
                );

                CREATE TABLE IF NOT EXISTS trend_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_name TEXT NOT NULL,
                    snapshot_date TEXT NOT NULL,
                    stars INTEGER NOT NULL,
                    language TEXT,
                    FOREIGN KEY(repo_name) REFERENCES repos(name)
                );
                """
            )
            conn.commit()

    def save_repo(self, repo: RepoItem) -> None:
        with closing(self.connect()) as conn:
            conn.execute(
                """
                INSERT INTO repos(name, url, description, language, stars)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    url=excluded.url,
                    description=excluded.description,
                    language=excluded.language,
                    stars=excluded.stars
                """,
                (repo.name, repo.url, repo.description, repo.language, repo.stars),
            )
            conn.commit()

    def save_skill(self, skill: SkillItem) -> None:
        with closing(self.connect()) as conn:
            conn.execute(
                "INSERT INTO skills(repo_name, skill_name, source_text) VALUES (?, ?, ?)",
                (skill.repo_name, skill.skill_name, skill.source_text),
            )
            conn.commit()

    def save_snapshot(self, snapshot: TrendSnapshot) -> None:
        with closing(self.connect()) as conn:
            conn.execute(
                """
                INSERT INTO trend_snapshot(repo_name, snapshot_date, stars, language)
                VALUES (?, ?, ?, ?)
                """,
                (
                    snapshot.repo_name,
                    snapshot.snapshot_date.isoformat(),
                    snapshot.stars,
                    snapshot.language,
                ),
            )
            conn.commit()

    def clear_all(self) -> None:
        with closing(self.connect()) as conn:
            conn.execute("DELETE FROM trend_snapshot")
            conn.execute("DELETE FROM skills")
            conn.execute("DELETE FROM repos")
            conn.commit()

    def list_repos(self) -> list[dict]:
        with closing(self.connect()) as conn:
            rows = conn.execute("SELECT * FROM repos ORDER BY stars DESC").fetchall()
        return [dict(row) for row in rows]

    def list_skills(self) -> list[dict]:
        with closing(self.connect()) as conn:
            rows = conn.execute("SELECT * FROM skills ORDER BY skill_name").fetchall()
        return [dict(row) for row in rows]

    def list_snapshots(self) -> list[dict]:
        with closing(self.connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM trend_snapshot ORDER BY snapshot_date, repo_name"
            ).fetchall()
        return [dict(row) for row in rows]
