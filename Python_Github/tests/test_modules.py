from __future__ import annotations

import tempfile
import time
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from run_pipeline import TrendPipeline
from tech_trend_platform.analysis import Analyzer
from tech_trend_platform.cleaning import RegexCleaner, SkillExtractor
from tech_trend_platform.concurrency import PerformanceTester
from tech_trend_platform.config import ConfigManager
from tech_trend_platform.crawler import GithubTrendingSpider
from tech_trend_platform.database import DBManager
from tech_trend_platform.models import RepoItem, TrendSnapshot
from tech_trend_platform.visualization import Visualizer
from tech_trend_platform.web import DashboardController, SkillMatchController


def slow_double(value: int) -> int:
    time.sleep(0.01)
    return value * 2


class ModuleDemoTests(unittest.TestCase):
    def test_config_reads_defaults(self):
        config = ConfigManager(database_name="unit.db")
        self.assertEqual(config.database_path.name, "unit.db")

    def test_database_insert_and_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DBManager(Path(tmp) / "test.db")
            db.initialize()
            repo = RepoItem("owner/demo", "https://github.com/owner/demo", "Python Flask", "Python", 1200)
            db.save_repo(repo)
            db.save_snapshot(TrendSnapshot(repo.name, date(2026, 7, 8), repo.stars, repo.language))
            for skill in SkillExtractor().extract(repo):
                db.save_skill(skill)
            self.assertEqual(db.list_repos()[0]["name"], "owner/demo")
            self.assertTrue(db.list_skills())
            self.assertTrue(db.list_snapshots())

    def test_crawler_parses_sample_html(self):
        html = """
        <article>
          <h2><a href="/owner/demo"> owner / demo </a></h2>
          <p class="col-9 color-fg-muted my-1 pr-4">Python Flask dashboard</p>
          <span itemprop="programmingLanguage">Python</span>
          <a href="/owner/demo/stargazers" class="Link--muted d-inline-block mr-3">1.2k</a>
        </article>
        """
        repos = GithubTrendingSpider(ConfigManager()).parse(html)
        self.assertEqual(repos[0].name, "owner/demo")
        self.assertEqual(repos[0].stars, 1200)
        self.assertEqual(repos[0].language, "Python")

    def test_crawler_falls_back_to_api_when_html_layout_is_empty(self):
        spider = GithubTrendingSpider(ConfigManager())
        fake_repo = RepoItem("api/demo", "https://github.com/api/demo", "API fallback", "Python", 99)
        with patch.object(spider, "fetch_html", return_value="<html></html>"):
            with patch.object(spider, "fetch_from_search_api", return_value=[fake_repo]):
                repos = spider.crawl(limit=1)
        self.assertEqual(repos[0].name, "api/demo")

    def test_cleaner_and_skill_extractor(self):
        cleaner = RegexCleaner()
        self.assertEqual(cleaner.parse_star_count("2.5k stars"), 2500)
        self.assertEqual(cleaner.extract_versions("Python 3.12.1 and Flask 2.3"), ["3.12.1", "2.3"])
        repo = RepoItem("demo", "url", "Build with Python and SQLite", "Python", 10)
        names = [skill.skill_name for skill in SkillExtractor().extract(repo)]
        self.assertIn("Python", names)
        self.assertIn("SQLite", names)

    def test_performance_tester_outputs_modes(self):
        results = PerformanceTester().compare([1, 2, 3], slow_double, max_workers=2)
        self.assertEqual([result.mode for result in results], ["single_thread", "thread_pool"])

    def test_analyzer_and_visualizer(self):
        analyzer = Analyzer()
        repos = [{"name": "a", "language": "Python", "stars": 10}]
        skills = [{"repo_name": "a", "skill_name": "Python"}]
        snapshots = [{"repo_name": "a", "snapshot_date": "2026-07-08", "stars": 10}]
        self.assertEqual(analyzer.language_ranking(repos), [("Python", 1)])
        self.assertEqual(analyzer.keyword_frequency(skills), [("Python", 1)])
        self.assertIn("a", analyzer.week_over_week_trend(snapshots))
        self.assertIn("<", Visualizer().bar_chart("语言排行", [("Python", 1)]))

    def test_skill_match_report_scores_user_stack(self):
        analyzer = Analyzer()
        repos = [
            {"name": "a", "language": "Python", "stars": 100},
            {"name": "b", "language": "TypeScript", "stars": 80},
        ]
        skills = [
            {"repo_name": "a", "skill_name": "Flask"},
            {"repo_name": "b", "skill_name": "React"},
        ]
        report = analyzer.skill_match_report(["Python", "Flask"], skills, repos)
        self.assertGreater(report["match_percent"], 0)
        self.assertTrue(report["missing_skills"])
        self.assertTrue(report["recommendations"])

    def test_web_controllers_render_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DBManager(Path(tmp) / "test.db")
            db.initialize()
            repo = RepoItem("owner/demo", "url", "Python Flask", "Python", 100)
            db.save_repo(repo)
            for skill in SkillExtractor().extract(repo):
                db.save_skill(skill)
            db.save_snapshot(TrendSnapshot(repo.name, date(2026, 7, 8), repo.stars, repo.language))
            analyzer = Analyzer()
            visualizer = Visualizer()
            self.assertIn("开发者技术趋势画像", DashboardController(db, analyzer, visualizer).render())
            self.assertIn("我的技能对标", SkillMatchController(db, analyzer, visualizer).render(["Python"]))

    def test_pipeline_generates_dashboard_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(project_root=Path(tmp), database_name="pipeline.db")
            output_path = TrendPipeline(config).run(use_network=False)
            self.assertTrue(output_path.exists())
            html = output_path.read_text(encoding="utf-8")
            self.assertIn("开发者技术趋势画像与个人技能对标平台", html)
            self.assertIn("仓库数据表", html)
            self.assertIn("分析匹配度", html)

    def test_pipeline_strict_network_raises_when_crawl_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigManager(project_root=Path(tmp), database_name="pipeline.db")
            pipeline = TrendPipeline(config)
            with patch("run_pipeline.GithubTrendingSpider") as spider_class:
                spider_class.return_value.crawl.side_effect = RuntimeError("offline")
                with self.assertRaises(RuntimeError):
                    pipeline.run(use_network=True, allow_sample_fallback=False)


if __name__ == "__main__":
    unittest.main()
