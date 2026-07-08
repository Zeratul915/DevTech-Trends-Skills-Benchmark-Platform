from __future__ import annotations

import sys
from datetime import date, timedelta

from tech_trend_platform.analysis import Analyzer
from tech_trend_platform.cleaning import SkillExtractor
from tech_trend_platform.config import ConfigManager
from tech_trend_platform.database import DBManager
from tech_trend_platform.models import RepoItem, TrendSnapshot
from tech_trend_platform.visualization import Visualizer
from tech_trend_platform.web import DashboardController, SkillMatchController


def build_demo_database() -> DBManager:
    config = ConfigManager(database_name="demo_trends.db")
    config.ensure_dirs()
    if config.database_path.exists():
        config.database_path.unlink()
    db = DBManager(config.database_path)
    db.initialize()

    repos = [
        RepoItem("pallets/flask", "https://github.com/pallets/flask", "Python web framework", "Python", 68000),
        RepoItem("scrapy/scrapy", "https://github.com/scrapy/scrapy", "Fast Scrapy crawler", "Python", 54000),
        RepoItem("facebook/react", "https://github.com/facebook/react", "JavaScript UI library", "JavaScript", 225000),
    ]
    extractor = SkillExtractor()
    for repo in repos:
        db.save_repo(repo)
        for skill in extractor.extract(repo):
            db.save_skill(skill)
        for offset in range(2):
            db.save_snapshot(
                TrendSnapshot(
                    repo_name=repo.name,
                    snapshot_date=date.today() - timedelta(days=7 * offset),
                    stars=repo.stars - offset * 100,
                    language=repo.language,
                )
            )
    return db


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    db = build_demo_database()
    analyzer = Analyzer()
    visualizer = Visualizer()
    dashboard = DashboardController(db, analyzer, visualizer)
    skill_match = SkillMatchController(db, analyzer, visualizer)
    print(dashboard.render()[:500])
    print(skill_match.render(["Python", "Flask"])[:500])


if __name__ == "__main__":
    main()
