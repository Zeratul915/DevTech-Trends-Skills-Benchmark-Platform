from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


class Analyzer:
    """Turns stored trend records into dashboard-ready statistics."""

    SKILL_CATEGORIES = {
        "Python": "后端 / 数据分析",
        "Java": "后端开发",
        "JavaScript": "前端开发",
        "TypeScript": "前端工程化",
        "Go": "云原生 / 后端",
        "Rust": "系统编程",
        "Shell": "自动化运维",
        "C#": "桌面 / 企业开发",
        "C++": "系统 / 性能开发",
        "Flask": "Python Web",
        "Django": "Python Web",
        "Scrapy": "爬虫采集",
        "React": "前端开发",
        "Vue": "前端开发",
        "Next.js": "前端工程化",
        "Node.js": "后端 / 全栈",
        "SQLite": "数据库",
        "PostgreSQL": "数据库",
        "MySQL": "数据库",
        "Redis": "缓存 / 数据库",
        "Pandas": "数据分析",
        "Docker": "工程部署",
        "Kubernetes": "云原生",
        "Argo CD": "DevOps",
        "Prisma": "数据库 ORM",
        "GitHub": "工程协作",
        "AI": "人工智能",
        "LLM": "人工智能",
        "Agent": "人工智能",
        "Machine Learning": "人工智能",
    }

    def language_ranking(self, repos: list[dict]) -> list[tuple[str, int]]:
        counter = Counter(repo.get("language") or "Unknown" for repo in repos)
        return counter.most_common()

    def keyword_frequency(self, skills: list[dict]) -> list[tuple[str, int]]:
        counter = Counter(skill["skill_name"] for skill in skills)
        return counter.most_common()

    def week_over_week_trend(self, snapshots: list[dict]) -> dict[str, list[tuple[str, int]]]:
        grouped: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for row in snapshots:
            grouped[row["repo_name"]].append((row["snapshot_date"], int(row["stars"])))
        return {name: sorted(values) for name, values in grouped.items()}

    def hot_skill_scores(self, skills: list[dict], repos: list[dict]) -> list[tuple[str, int]]:
        repo_stars = {repo["name"]: int(repo.get("stars") or 0) for repo in repos}
        scores: Counter[str] = Counter()
        for skill in skills:
            scores[skill["skill_name"]] += max(repo_stars.get(skill["repo_name"], 0), 1)

        # Languages are also part of a developer's skill stack. Add them with a
        # smaller weight so the matching page still works when descriptions do
        # not contain many explicit keywords.
        for repo in repos:
            language = repo.get("language") or "Unknown"
            if language != "Unknown":
                scores[language] += max(int(repo.get("stars") or 0) // 2, 1)
        return scores.most_common()

    def skill_gap(self, user_skills: list[str], hot_scores: list[tuple[str, int]]) -> list[str]:
        owned = {skill.lower() for skill in user_skills}
        return [skill for skill, _score in hot_scores if skill.lower() not in owned][:5]

    def skill_match_report(
        self,
        user_skills: list[str],
        skills: list[dict],
        repos: list[dict],
        top_n: int = 12,
    ) -> dict[str, Any]:
        hot_scores = self.hot_skill_scores(skills, repos)[:top_n]
        owned = {skill.strip().lower() for skill in user_skills if skill.strip()}
        total_score = sum(score for _skill, score in hot_scores) or 1
        owned_score = sum(score for skill, score in hot_scores if skill.lower() in owned)
        match_percent = round(owned_score / total_score * 100)

        matched = [
            {"skill": skill, "score": score, "category": self.category_for(skill)}
            for skill, score in hot_scores
            if skill.lower() in owned
        ]
        missing = [
            {"skill": skill, "score": score, "category": self.category_for(skill)}
            for skill, score in hot_scores
            if skill.lower() not in owned
        ]
        category_gaps: Counter[str] = Counter()
        for item in missing:
            category_gaps[item["category"]] += item["score"]

        return {
            "match_percent": match_percent,
            "level": self._match_level(match_percent),
            "selected_skills": sorted(user_skills),
            "matched_skills": matched,
            "missing_skills": missing[:6],
            "category_gaps": [
                {"category": category, "score": score}
                for category, score in category_gaps.most_common(5)
            ],
            "recommendations": self._recommendations(missing[:5]),
            "hot_skills": [
                {"skill": skill, "score": score, "category": self.category_for(skill)}
                for skill, score in hot_scores
            ],
        }

    def available_skill_options(self, skills: list[dict], repos: list[dict]) -> list[str]:
        names = {skill for skill, _score in self.hot_skill_scores(skills, repos)}
        names.update(repo.get("language") for repo in repos if repo.get("language"))
        return sorted(name for name in names if name and name != "Unknown")

    def category_for(self, skill: str) -> str:
        return self.SKILL_CATEGORIES.get(skill, "通用技术")

    @staticmethod
    def _match_level(match_percent: int) -> str:
        if match_percent >= 80:
            return "高度匹配"
        if match_percent >= 55:
            return "中等匹配"
        if match_percent >= 30:
            return "基础匹配"
        return "需要补强"

    def _recommendations(self, missing: list[dict[str, Any]]) -> list[str]:
        if not missing:
            return ["你的技能栈已经覆盖当前趋势中的主要方向，可以继续做项目沉淀和深度优化。"]
        return [
            f"优先学习 {item['skill']}，它属于「{item['category']}」方向，在当前 GitHub 趋势数据中热度较高。"
            for item in missing
        ]
