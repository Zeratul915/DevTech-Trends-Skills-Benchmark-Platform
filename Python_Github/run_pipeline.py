from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

from tech_trend_platform.analysis import Analyzer
from tech_trend_platform.cleaning import SkillExtractor
from tech_trend_platform.config import ConfigManager
from tech_trend_platform.crawler import GithubTrendingSpider
from tech_trend_platform.database import DBManager
from tech_trend_platform.models import RepoItem, TrendSnapshot
from tech_trend_platform.visualization import Visualizer
from tech_trend_platform.web import (
    DashboardController,
    SkillMatchController,
    render_interactive_page,
)


SAMPLE_REPOS = [
    RepoItem(
        name="pallets/flask",
        url="https://github.com/pallets/flask",
        description="The Python micro framework for building web applications.",
        language="Python",
        stars=68000,
    ),
    RepoItem(
        name="scrapy/scrapy",
        url="https://github.com/scrapy/scrapy",
        description="A fast high-level web crawling and scraping framework for Python.",
        language="Python",
        stars=54000,
    ),
    RepoItem(
        name="facebook/react",
        url="https://github.com/facebook/react",
        description="The library for web and native user interfaces with JavaScript.",
        language="JavaScript",
        stars=225000,
    ),
    RepoItem(
        name="pandas-dev/pandas",
        url="https://github.com/pandas-dev/pandas",
        description="Powerful data structures for data analysis in Python.",
        language="Python",
        stars=45000,
    ),
    RepoItem(
        name="docker/compose",
        url="https://github.com/docker/compose",
        description="Define and run multi-container applications with Docker.",
        language="Go",
        stars=35000,
    ),
]


class TrendPipeline:
    """Coordinates crawling, cleaning, persistence, analysis, and static output."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.db = DBManager(config.database_path)
        self.extractor = SkillExtractor()
        self.data_source = "sample"

    def run(
        self,
        use_network: bool = False,
        limit: int = 15,
        allow_sample_fallback: bool = True,
        user_skills: list[str] | None = None,
    ) -> Path:
        self.config.ensure_dirs()
        self.db.initialize()
        self.db.clear_all()
        repos = self._load_repos(use_network, limit, allow_sample_fallback)
        self._save_repos(repos)
        return self._render_output(user_skills or ["Python", "Flask", "SQLite"])

    def _load_repos(
        self,
        use_network: bool,
        limit: int,
        allow_sample_fallback: bool,
    ) -> list[RepoItem]:
        if not use_network:
            self.data_source = "sample"
            return SAMPLE_REPOS[:limit]

        try:
            repos = GithubTrendingSpider(self.config).crawl(limit=limit)
        except Exception as exc:
            if not allow_sample_fallback:
                raise RuntimeError(f"真实 GitHub 数据抓取失败: {exc}") from exc
            self.data_source = f"sample_fallback: {exc}"
            return SAMPLE_REPOS[:limit]

        if not repos:
            if not allow_sample_fallback:
                raise RuntimeError("真实 GitHub 数据抓取失败: 没有解析到任何仓库")
            self.data_source = "sample_fallback: no repositories parsed"
            return SAMPLE_REPOS[:limit]

        self.data_source = "github"
        return repos

    def _save_repos(self, repos: list[RepoItem]) -> None:
        today = date.today()
        for repo in repos:
            self.db.save_repo(repo)
            for skill in self.extractor.extract(repo):
                self.db.save_skill(skill)
            for offset in range(3):
                self.db.save_snapshot(
                    TrendSnapshot(
                        repo_name=repo.name,
                        snapshot_date=today - timedelta(days=offset * 7),
                        stars=max(repo.stars - offset * 150, 0),
                        language=repo.language,
                    )
                )

    def _render_output(self, user_skills: list[str]) -> Path:
        analyzer = Analyzer()
        visualizer = Visualizer()
        dashboard = DashboardController(self.db, analyzer, visualizer)
        skill_match = SkillMatchController(self.db, analyzer, visualizer)
        data_source_label = "真实 GitHub 数据" if self.data_source == "github" else "示例数据"
        html = render_interactive_page(
            summary=dashboard.summary(),
            skill_options=skill_match.available_skills(),
            initial_report=skill_match.report(user_skills),
            api_mode=False,
            data_source=data_source_label,
        )
        output_dir = self.config.project_root / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "dashboard.html"
        output_path.write_text(html, encoding="utf-8")
        return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抓取 GitHub 数据并生成成果页")
    parser.add_argument("--network", action="store_true", help="联网抓取真实 GitHub 数据")
    parser.add_argument("--strict-network", action="store_true", help="真实抓取失败时直接报错，不使用示例数据兜底")
    parser.add_argument("--limit", type=int, default=15, help="抓取仓库数量")
    parser.add_argument(
        "--skills",
        default="Python,Flask,SQLite",
        help="个人技能列表，用英文逗号分隔，例如 Python,React,Docker",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ConfigManager()
    pipeline = TrendPipeline(config)
    output_path = pipeline.run(
        use_network=args.network,
        limit=args.limit,
        allow_sample_fallback=not args.strict_network,
        user_skills=[skill.strip() for skill in args.skills.split(",") if skill.strip()],
    )
    print(f"成果页已生成: {output_path}")
    print(f"数据库位置: {config.database_path}")
    print(f"数据来源: {pipeline.data_source}")


if __name__ == "__main__":
    main()
