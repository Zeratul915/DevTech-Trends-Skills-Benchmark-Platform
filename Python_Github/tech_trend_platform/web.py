from __future__ import annotations

import json
from html import escape

from .analysis import Analyzer
from .database import DBManager
from .visualization import Visualizer


class DashboardController:
    """Prepares data for the dashboard page."""

    def __init__(self, db: DBManager, analyzer: Analyzer, visualizer: Visualizer):
        self.db = db
        self.analyzer = analyzer
        self.visualizer = visualizer

    def render(self) -> str:
        repos = self.db.list_repos()
        skills = self.db.list_skills()
        snapshots = self.db.list_snapshots()
        return "\n".join(
            [
                "<h1>开发者技术趋势画像</h1>",
                self.visualizer.bar_chart("语言排行", self.analyzer.language_ranking(repos)),
                self.visualizer.word_cloud("技能关键词", self.analyzer.keyword_frequency(skills)),
                self.visualizer.line_chart("趋势折线", self.analyzer.week_over_week_trend(snapshots)),
            ]
        )

    def summary(self) -> dict:
        repos = self.db.list_repos()
        skills = self.db.list_skills()
        snapshots = self.db.list_snapshots()
        return {
            "repo_count": len(repos),
            "skill_count": len(skills),
            "language_ranking": self.analyzer.language_ranking(repos),
            "keyword_frequency": self.analyzer.keyword_frequency(skills),
            "trend": self.analyzer.week_over_week_trend(snapshots),
            "repos": repos,
        }


class SkillMatchController:
    """Prepares user skill comparison content."""

    def __init__(self, db: DBManager, analyzer: Analyzer, visualizer: Visualizer):
        self.db = db
        self.analyzer = analyzer
        self.visualizer = visualizer

    def available_skills(self) -> list[str]:
        return self.analyzer.available_skill_options(self.db.list_skills(), self.db.list_repos())

    def report(self, user_skills: list[str]) -> dict:
        return self.analyzer.skill_match_report(
            user_skills=user_skills,
            skills=self.db.list_skills(),
            repos=self.db.list_repos(),
        )

    def render(self, user_skills: list[str]) -> str:
        report = self.report(user_skills)
        suggestions = "".join(f"<li>{escape(text)}</li>" for text in report["recommendations"])
        missing = "".join(
            f"<li>{escape(item['skill'])} <span>{escape(item['category'])}</span></li>"
            for item in report["missing_skills"]
        )
        return (
            "<h1>我的技能对标</h1>"
            f"<p>匹配度：{report['match_percent']}%（{escape(report['level'])}）</p>"
            f"<h2>需要补强</h2><ul>{missing}</ul>"
            f"<h2>学习建议</h2><ul>{suggestions}</ul>"
        )


class FlaskApp:
    """Wires controllers into Flask routes."""

    def __init__(self, dashboard: DashboardController, skill_match: SkillMatchController):
        self.dashboard = dashboard
        self.skill_match = skill_match

    def create_app(self):
        try:
            from flask import Flask, jsonify, request
        except Exception as exc:
            raise RuntimeError("Flask is not installed. Install flask to run the web app.") from exc

        app = Flask(__name__)

        @app.get("/")
        def index():
            return render_interactive_page(
                summary=self.dashboard.summary(),
                skill_options=self.skill_match.available_skills(),
                initial_report=self.skill_match.report(["Python", "Flask", "SQLite"]),
                api_mode=True,
            )

        @app.get("/api/summary")
        def api_summary():
            return jsonify(self.dashboard.summary())

        @app.get("/api/skills")
        def api_skills():
            return jsonify({"skills": self.skill_match.available_skills()})

        @app.post("/api/skill-match")
        def api_skill_match():
            payload = request.get_json(silent=True) or {}
            user_skills = payload.get("skills", [])
            if not isinstance(user_skills, list):
                user_skills = []
            return jsonify(self.skill_match.report([str(skill) for skill in user_skills]))

        @app.get("/skill-match")
        def skill_match_page():
            user_skills = request.args.get("skills", "Python,Flask").split(",")
            return self.skill_match.render([skill.strip() for skill in user_skills if skill.strip()])

        @app.get("/api/trend")
        def api_trend():
            return jsonify(self.dashboard.db.list_snapshots())

        return app


def render_interactive_page(
    summary: dict,
    skill_options: list[str],
    initial_report: dict,
    api_mode: bool,
    data_source: str = "数据库",
) -> str:
    repo_rows = "\n".join(
        "<tr>"
        f"<td><a href=\"{escape(repo['url'])}\">{escape(repo['name'])}</a></td>"
        f"<td>{escape(repo.get('language') or 'Unknown')}</td>"
        f"<td>{int(repo.get('stars') or 0):,}</td>"
        f"<td>{escape(repo.get('description') or '')}</td>"
        "</tr>"
        for repo in summary["repos"][:20]
    )
    skill_buttons = "\n".join(
        "<label class=\"skill-chip\">"
        f"<input type=\"checkbox\" value=\"{escape(skill)}\">"
        f"<span>{escape(skill)}</span>"
        "</label>"
        for skill in skill_options
    )
    language_items = "".join(
        f"<li><strong>{escape(language)}</strong><span>{count}</span></li>"
        for language, count in summary["language_ranking"][:8]
    )
    keyword_items = "".join(
        f"<li><strong>{escape(skill)}</strong><span>{score}</span></li>"
        for skill, score in summary["keyword_frequency"][:10]
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>开发者技术趋势画像平台</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --text: #20242a;
      --muted: #667085;
      --line: #d9e0e8;
      --accent: #0969da;
      --accent-soft: #ddf4ff;
      --good: #1a7f37;
      --warn: #bf8700;
      --danger: #cf222e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, "Microsoft YaHei", sans-serif;
    }}
    header {{
      background: #20242a;
      color: white;
      padding: 28px 36px;
    }}
    header h1 {{ margin: 0 0 8px; font-size: 28px; }}
    header p {{ margin: 0; color: #d0d7de; }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px 18px 48px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .stat, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .stat span {{ display: block; color: var(--muted); font-size: 13px; }}
    .stat strong {{ display: block; margin-top: 8px; font-size: 26px; }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr);
      gap: 18px;
      align-items: start;
    }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    h3 {{ margin: 18px 0 10px; font-size: 16px; }}
    .skill-picker {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      max-height: 260px;
      overflow: auto;
      padding-right: 4px;
    }}
    .skill-chip input {{ position: absolute; opacity: 0; }}
    .skill-chip span {{
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      background: #f8fafc;
      cursor: pointer;
      user-select: none;
      font-size: 14px;
    }}
    .skill-chip input:checked + span {{
      background: var(--accent-soft);
      border-color: #54aeef;
      color: var(--accent);
      font-weight: 700;
    }}
    .actions {{ display: flex; gap: 10px; margin-top: 16px; }}
    button {{
      border: 0;
      border-radius: 7px;
      padding: 10px 14px;
      background: var(--accent);
      color: white;
      cursor: pointer;
      font-weight: 700;
    }}
    button.secondary {{
      background: #eef2f6;
      color: var(--text);
    }}
    .score-wrap {{
      display: grid;
      grid-template-columns: 140px minmax(0, 1fr);
      gap: 18px;
      align-items: center;
    }}
    .score-circle {{
      width: 132px;
      height: 132px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: conic-gradient(var(--accent) calc(var(--score) * 1%), #eaeef2 0);
    }}
    .score-inner {{
      width: 96px;
      height: 96px;
      border-radius: 50%;
      background: white;
      display: grid;
      place-items: center;
      text-align: center;
      font-weight: 800;
      font-size: 24px;
    }}
    .result-list, .rank-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 8px;
    }}
    .result-list li, .rank-list li {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1px solid #edf1f5;
      padding: 8px 0;
    }}
    .result-list span, .rank-list span {{ color: var(--muted); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: #f8fafc; }}
    a {{ color: var(--accent); text-decoration: none; }}
    .subgrid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      margin-top: 18px;
    }}
    .badge {{
      display: inline-flex;
      border: 1px solid #54aeef;
      background: var(--accent-soft);
      color: var(--accent);
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 13px;
    }}
    @media (max-width: 860px) {{
      .stats, .grid, .subgrid, .score-wrap {{ grid-template-columns: 1fr; }}
      header {{ padding: 22px 18px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>开发者技术趋势画像与个人技能对标平台</h1>
    <p>数据来源：{escape(data_source)}。勾选你掌握的技术栈，系统会根据当前 GitHub 趋势计算匹配度和学习建议。</p>
  </header>
  <main>
    <div class="stats">
      <div class="stat"><span>仓库数量</span><strong>{summary["repo_count"]}</strong></div>
      <div class="stat"><span>技能记录</span><strong>{summary["skill_count"]}</strong></div>
      <div class="stat"><span>可选技术栈</span><strong>{len(skill_options)}</strong></div>
    </div>
    <div class="grid">
      <section class="panel">
        <h2>选择你掌握的技术栈</h2>
        <div class="skill-picker" id="skillPicker">{skill_buttons}</div>
        <div class="actions">
          <button id="analyzeBtn" type="button">分析匹配度</button>
          <button class="secondary" id="clearBtn" type="button">清空选择</button>
        </div>
      </section>
      <section class="panel">
        <h2>匹配结果</h2>
        <div id="matchResult"></div>
      </section>
    </div>
    <div class="subgrid">
      <section class="panel">
        <h2>语言排行</h2>
        <ul class="rank-list">{language_items}</ul>
      </section>
      <section class="panel">
        <h2>技能关键词热度</h2>
        <ul class="rank-list">{keyword_items}</ul>
      </section>
    </div>
    <section class="panel" style="margin-top:18px">
      <h2>仓库数据表</h2>
      <table>
        <thead><tr><th>仓库</th><th>语言</th><th>Stars</th><th>描述</th></tr></thead>
        <tbody>{repo_rows}</tbody>
      </table>
    </section>
  </main>
  <script>
    window.INITIAL_REPORT = {json.dumps(initial_report, ensure_ascii=False)};
    window.HOT_SKILLS = {json.dumps(initial_report.get("hot_skills", []), ensure_ascii=False)};
    window.API_MODE = {json.dumps(api_mode)};
  </script>
  <script>
    const picker = document.getElementById('skillPicker');
    const resultBox = document.getElementById('matchResult');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const clearBtn = document.getElementById('clearBtn');

    function selectedSkills() {{
      return [...picker.querySelectorAll('input:checked')].map(input => input.value);
    }}

    function categoryFor(skill) {{
      const found = window.HOT_SKILLS.find(item => item.skill.toLowerCase() === skill.toLowerCase());
      return found ? found.category : '通用技术';
    }}

    window.calculateStaticReport = function(skills) {{
      const owned = new Set(skills.map(skill => skill.toLowerCase()));
      const total = window.HOT_SKILLS.reduce((sum, item) => sum + item.score, 0) || 1;
      const ownedScore = window.HOT_SKILLS
        .filter(item => owned.has(item.skill.toLowerCase()))
        .reduce((sum, item) => sum + item.score, 0);
      const match = Math.round(ownedScore / total * 100);
      const missing = window.HOT_SKILLS
        .filter(item => !owned.has(item.skill.toLowerCase()))
        .slice(0, 6);
      const gapMap = new Map();
      missing.forEach(item => gapMap.set(item.category, (gapMap.get(item.category) || 0) + item.score));
      const gaps = [...gapMap.entries()]
        .map(([category, score]) => ({{category, score}}))
        .sort((a, b) => b.score - a.score);
      const level = match >= 80 ? '高度匹配' : match >= 55 ? '中等匹配' : match >= 30 ? '基础匹配' : '需要补强';
      const recommendations = missing.length
        ? missing.slice(0, 5).map(item => `优先学习 ${{item.skill}}，它属于「${{item.category}}」方向，在当前 GitHub 趋势数据中热度较高。`)
        : ['你的技能栈已经覆盖当前趋势中的主要方向，可以继续做项目沉淀和深度优化。'];
      return {{
        match_percent: match,
        level,
        selected_skills: skills,
        matched_skills: window.HOT_SKILLS.filter(item => owned.has(item.skill.toLowerCase())),
        missing_skills: missing,
        category_gaps: gaps,
        recommendations,
        hot_skills: window.HOT_SKILLS
      }};
    }};

    function renderReport(report) {{
      const missing = report.missing_skills.map(item =>
        `<li><strong>${{item.skill}}</strong><span>${{item.category}}</span></li>`
      ).join('');
      const gaps = report.category_gaps.map(item =>
        `<li><strong>${{item.category}}</strong><span>${{item.score}}</span></li>`
      ).join('');
      const recommendations = report.recommendations.map(text => `<li>${{text}}</li>`).join('');
      resultBox.innerHTML = `
        <div class="score-wrap">
          <div class="score-circle" style="--score:${{report.match_percent}}">
            <div class="score-inner">${{report.match_percent}}%</div>
          </div>
          <div>
            <span class="badge">${{report.level}}</span>
            <h3>需要补强的技术</h3>
            <ul class="result-list">${{missing || '<li><strong>暂无明显短板</strong><span>继续深入项目实践</span></li>'}}</ul>
          </div>
        </div>
        <h3>短板方向</h3>
        <ul class="result-list">${{gaps || '<li><strong>覆盖较全面</strong><span>保持学习节奏</span></li>'}}</ul>
        <h3>学习建议</h3>
        <ul class="result-list">${{recommendations}}</ul>
      `;
    }}

    async function analyze() {{
      const skills = selectedSkills();
      if (window.API_MODE) {{
        const res = await fetch('/api/skill-match', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{skills}})
        }});
        renderReport(await res.json());
      }} else {{
        renderReport(window.calculateStaticReport(skills));
      }}
    }}

    clearBtn.addEventListener('click', () => {{
      picker.querySelectorAll('input').forEach(input => input.checked = false);
      analyze();
    }});
    analyzeBtn.addEventListener('click', analyze);
    const initialSelected = new Set((window.INITIAL_REPORT.selected_skills || []).map(skill => skill.toLowerCase()));
    picker.querySelectorAll('input').forEach(input => {{
      input.checked = initialSelected.has(input.value.toLowerCase());
    }});
    renderReport(window.INITIAL_REPORT);
  </script>
</body>
</html>"""
