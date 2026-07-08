from __future__ import annotations

import re

from .models import RepoItem, SkillItem


class RegexCleaner:
    """Small reusable regular-expression helpers."""

    STAR_PATTERN = re.compile(r"([\d,.]+)\s*(k|K)?")
    VERSION_PATTERN = re.compile(r"\b\d+(?:\.\d+){1,3}\b")
    TAG_PATTERN = re.compile(r"<[^>]+>")
    SPACE_PATTERN = re.compile(r"\s+")

    def clean_text(self, text: str) -> str:
        without_tags = self.TAG_PATTERN.sub(" ", text)
        return self.SPACE_PATTERN.sub(" ", without_tags).strip()

    def parse_star_count(self, text: str) -> int:
        match = self.STAR_PATTERN.search(text.replace(",", ""))
        if not match:
            return 0
        number = float(match.group(1))
        if match.group(2):
            number *= 1000
        return int(number)

    def extract_versions(self, text: str) -> list[str]:
        return self.VERSION_PATTERN.findall(text)


class SkillExtractor:
    """Extracts technology keywords from repository text."""

    DEFAULT_KEYWORDS = [
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "Go",
        "Rust",
        "Shell",
        "C#",
        "C++",
        "Flask",
        "Django",
        "Scrapy",
        "React",
        "Vue",
        "Next.js",
        "Node.js",
        "SQLite",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "Pandas",
        "Docker",
        "Kubernetes",
        "Argo CD",
        "Prisma",
        "GitHub",
        "AI",
        "LLM",
        "Agent",
        "Machine Learning",
    ]

    def __init__(self, keywords: list[str] | None = None):
        self.keywords = keywords or self.DEFAULT_KEYWORDS

    def extract(self, repo: RepoItem) -> list[SkillItem]:
        text = f"{repo.name} {repo.description} {repo.language}"
        found: list[SkillItem] = []
        for keyword in self.keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE):
                found.append(
                    SkillItem(
                        repo_name=repo.name,
                        skill_name=keyword,
                        source_text=repo.description,
                    )
                )
        return found
