from __future__ import annotations

import json
import re
from datetime import date, timedelta
from html import unescape
from urllib.parse import quote
from urllib.request import Request, urlopen

from .cleaning import RegexCleaner
from .config import ConfigManager
from .models import RepoItem


class GithubTrendingSpider:
    """Discovers repositories from GitHub Trending.

    The first strategy scrapes the public Trending HTML page. If GitHub changes the
    page layout, the spider falls back to GitHub's public search API so the project
    can still download real GitHub repository data without a token.
    """

    ARTICLE_PATTERN = re.compile(r"<article\b[^>]*>(.*?)</article>", re.IGNORECASE | re.DOTALL)
    REPO_LINK_PATTERN = re.compile(
        r"<h2\b[^>]*>.*?<a\b[^>]*href=[\"']/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)[\"'][^>]*>",
        re.IGNORECASE | re.DOTALL,
    )
    DESCRIPTION_PATTERN = re.compile(
        r"<p\b[^>]*class=[\"'][^\"']*col-9[^\"']*[\"'][^>]*>(?P<text>.*?)</p>",
        re.IGNORECASE | re.DOTALL,
    )
    LANGUAGE_PATTERN = re.compile(
        r"<span\b[^>]*itemprop=[\"']programmingLanguage[\"'][^>]*>(?P<text>.*?)</span>",
        re.IGNORECASE | re.DOTALL,
    )
    STARS_PATTERN = re.compile(
        r"<a\b[^>]*href=[\"']/[\w.-]+/[\w.-]+/stargazers[\"'][^>]*>(?P<text>.*?)</a>",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self, config: ConfigManager):
        self.config = config
        self.cleaner = RegexCleaner()

    def fetch_html(self) -> str:
        request = Request(
            self.config.trending_url,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urlopen(request, timeout=self.config.request_timeout) as response:
            return response.read().decode("utf-8", errors="ignore")

    def parse(self, html: str) -> list[RepoItem]:
        repos: list[RepoItem] = []
        for article in self.ARTICLE_PATTERN.findall(html):
            repo = self._parse_article(article)
            if repo is not None:
                repos.append(repo)
        return self._deduplicate(repos)

    def crawl(self, limit: int = 15) -> list[RepoItem]:
        repos = self.parse(self.fetch_html())
        if repos:
            return repos[:limit]
        return self.fetch_from_search_api(limit=limit)

    def fetch_from_search_api(self, limit: int = 15) -> list[RepoItem]:
        since = (date.today() - timedelta(days=14)).isoformat()
        query = quote(f"created:>{since} stars:>50")
        url = (
            "https://api.github.com/search/repositories"
            f"?q={query}&sort=stars&order=desc&per_page={limit}"
        )
        request = Request(
            url,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "application/vnd.github+json",
            },
        )
        with urlopen(request, timeout=self.config.request_timeout) as response:
            payload = json.loads(response.read().decode("utf-8", errors="ignore"))

        repos = []
        for item in payload.get("items", []):
            repos.append(
                RepoItem(
                    name=item.get("full_name", "unknown/unknown"),
                    url=item.get("html_url", ""),
                    description=item.get("description") or "",
                    language=item.get("language") or "Unknown",
                    stars=int(item.get("stargazers_count") or 0),
                )
            )
        return repos

    def _parse_article(self, article: str) -> RepoItem | None:
        link_match = self.REPO_LINK_PATTERN.search(article)
        if not link_match:
            return None

        owner = link_match.group("owner")
        repo = link_match.group("repo")
        name = f"{owner}/{repo}"
        description = self._extract_text(article, self.DESCRIPTION_PATTERN)
        language = self._extract_text(article, self.LANGUAGE_PATTERN) or "Unknown"
        stars = self.cleaner.parse_star_count(self._extract_text(article, self.STARS_PATTERN))
        return RepoItem(
            name=name,
            url=f"https://github.com/{name}",
            description=description,
            language=language,
            stars=stars,
        )

    def _extract_text(self, html: str, pattern: re.Pattern[str]) -> str:
        match = pattern.search(html)
        if not match:
            return ""
        return self.cleaner.clean_text(unescape(match.group("text")))

    @staticmethod
    def _deduplicate(repos: list[RepoItem]) -> list[RepoItem]:
        unique: dict[str, RepoItem] = {}
        for repo in repos:
            unique[repo.name] = repo
        return list(unique.values())


class RepoDetailFetcher:
    """Fetches additional detail from one repository page."""

    TOPIC_PATTERN = re.compile(r'topic-tag[^>]*>\s*([^<]+)', flags=re.IGNORECASE)

    def __init__(self, config: ConfigManager):
        self.config = config

    def fetch_detail_html(self, repo: RepoItem) -> str:
        request = Request(repo.url, headers={"User-Agent": self.config.user_agent})
        with urlopen(request, timeout=self.config.request_timeout) as response:
            return response.read().decode("utf-8", errors="ignore")

    def extract_topics(self, html: str) -> list[str]:
        cleaner = RegexCleaner()
        return [cleaner.clean_text(topic) for topic in self.TOPIC_PATTERN.findall(html)]
