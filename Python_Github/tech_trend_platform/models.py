from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class RepoItem:
    """Repository information collected from GitHub Trending."""

    name: str
    url: str
    description: str = ""
    language: str = "Unknown"
    stars: int = 0


@dataclass
class SkillItem:
    """A technology keyword extracted from repository text."""

    repo_name: str
    skill_name: str
    source_text: str


@dataclass
class TrendSnapshot:
    """Daily trend score for a repository."""

    repo_name: str
    snapshot_date: date
    stars: int
    language: str
