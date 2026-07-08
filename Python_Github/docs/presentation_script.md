# Stage2 类设计汇报提纲

## 1. 开场定位

我们做的是“开发者技术趋势画像与个人技能对标平台”。它不是单独的爬虫练习，而是一条完整的数据管道：抓取 GitHub Trending，清洗成结构化数据，存入 SQLite，再做趋势分析和图表展示。

## 2. 类设计主线

汇报时按数据流讲类，不要按文件名硬背：

1. `GithubTrendingSpider` 把网页变成 `RepoItem`。
2. `RegexCleaner` 和 `SkillExtractor` 把文本变成 `SkillItem`。
3. `DBManager` 把 `RepoItem`、`SkillItem`、`TrendSnapshot` 存进 SQLite。
4. `Analyzer` 把数据库记录变成统计结论。
5. `Visualizer` 把统计结论变成图表 HTML。
6. `DashboardController` 和 `SkillMatchController` 把图表组织成页面。

## 3. 必讲设计原则

- 单一职责：每个类只解决一类问题。
- 低耦合：爬虫不直接写 SQL，分析不直接写页面。
- 可扩展：以后换数据源只改爬虫，换图表库只改可视化类。
- 可测试：每个模块都有一个最小测试，能单独证明它能工作。

## 4. 三人分工讲法

- 罗梓轩讲爬虫与清洗：`GithubTrendingSpider`、`RepoDetailFetcher`、`RegexCleaner`、`SkillExtractor`。
- 卢禹辰讲后端与数据：`DBManager`、`Analyzer`、`PerformanceTester`。
- 陈载阳讲展示与交互：`Visualizer`、`DashboardController`、`SkillMatchController`、`FlaskApp`。

## 5. 现场演示顺序

```powershell
python -m unittest discover -s tests
python demo.py
```

第一条命令说明每个模块都能独立通过测试。第二条命令说明内置示例数据可以跑通 dashboard 和技能对标结果。
