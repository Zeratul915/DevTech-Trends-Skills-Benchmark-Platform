from __future__ import annotations

from run_pipeline import TrendPipeline
from tech_trend_platform.analysis import Analyzer
from tech_trend_platform.config import ConfigManager
from tech_trend_platform.database import DBManager
from tech_trend_platform.visualization import Visualizer
from tech_trend_platform.web import DashboardController, FlaskApp, SkillMatchController


def create_app():
    config = ConfigManager()
    db = DBManager(config.database_path)
    db.initialize()
    if not db.list_repos():
        TrendPipeline(config).run(use_network=False)

    analyzer = Analyzer()
    visualizer = Visualizer()
    dashboard = DashboardController(db, analyzer, visualizer)
    skill_match = SkillMatchController(db, analyzer, visualizer)
    return FlaskApp(dashboard, skill_match).create_app()


if __name__ == "__main__":
    create_app().run(debug=True)
