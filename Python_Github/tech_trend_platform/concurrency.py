from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class ConcurrentCrawler:
    """Runs the same task with different concurrency strategies."""

    def run_single_thread(self, items: Iterable[T], task: Callable[[T], R]) -> list[R]:
        return [task(item) for item in items]

    def run_thread_pool(
        self, items: Iterable[T], task: Callable[[T], R], max_workers: int = 5
    ) -> list[R]:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            return list(pool.map(task, items))

    def run_process_pool(
        self, items: Iterable[T], task: Callable[[T], R], max_workers: int = 2
    ) -> list[R]:
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            return list(pool.map(task, items))


@dataclass
class PerformanceResult:
    mode: str
    seconds: float
    item_count: int


class PerformanceTester:
    """Measures single-thread, thread-pool, and process-pool cost."""

    def __init__(self, crawler: ConcurrentCrawler | None = None):
        self.crawler = crawler or ConcurrentCrawler()

    def compare(
        self,
        items: list[T],
        task: Callable[[T], R],
        max_workers: int = 4,
        include_process: bool = False,
    ) -> list[PerformanceResult]:
        results = [
            self._measure(
                "single_thread",
                lambda: self.crawler.run_single_thread(items, task),
                len(items),
            ),
            self._measure(
                "thread_pool",
                lambda: self.crawler.run_thread_pool(items, task, max_workers),
                len(items),
            ),
        ]
        if include_process:
            results.append(
                self._measure(
                    "process_pool",
                    lambda: self.crawler.run_process_pool(items, task, max_workers),
                    len(items),
                )
            )
        return results

    @staticmethod
    def _measure(mode: str, runner: Callable[[], object], count: int) -> PerformanceResult:
        start = time.perf_counter()
        runner()
        return PerformanceResult(mode=mode, seconds=time.perf_counter() - start, item_count=count)
