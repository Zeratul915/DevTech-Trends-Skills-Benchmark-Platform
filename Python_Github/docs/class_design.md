# 类设计总览

> 说明：这份文档不使用 Mermaid，所有图都用纯 Markdown / 文本表格表示，避免 UML 图在 Markdown 查看器里渲染异常。

## 1. 项目整体架构

项目主题：**开发者技术趋势画像与个人技能对标平台**

```text
GitHub Trending / GitHub Search API
        |
        v
[数据采集层]
GithubTrendingSpider / RepoDetailFetcher
        |
        v
[数据清洗层]
RegexCleaner / SkillExtractor
        |
        v
[数据存储层]
RepoItem / SkillItem / TrendSnapshot / DBManager
        |
        v
[数据分析层]
Analyzer / PerformanceTester
        |
        v
[可视化层]
Visualizer
        |
        v
[Web 展示层]
DashboardController / SkillMatchController / FlaskApp
        |
        v
[成果生成]
TrendPipeline -> outputs/dashboard.html
```

## 2. 核心类职责表

| 模块 | 类名 | 主要职责 | 主要输入 | 主要输出 |
| --- | --- | --- | --- | --- |
| 基础工具 | `ConfigManager` | 管理路径、数据库名、请求参数 | 默认配置 | 数据库路径、抓取参数 |
| 基础工具 | `LoggerFactory` | 统一日志格式 | 日志名称 | logger 对象 |
| 数据模型 | `RepoItem` | 表示一个仓库 | 爬虫解析结果 | 仓库对象 |
| 数据模型 | `SkillItem` | 表示一个技能关键词 | 仓库描述文本 | 技能对象 |
| 数据模型 | `TrendSnapshot` | 表示某天趋势快照 | 仓库热度数据 | 趋势快照对象 |
| 数据库 | `DBManager` | 建表、存储、查询 | 数据对象 | SQLite 记录 / 查询结果 |
| 爬虫 | `GithubTrendingSpider` | 抓取 Trending 或 API 仓库数据 | GitHub HTML / JSON | `RepoItem` 列表 |
| 爬虫 | `RepoDetailFetcher` | 抓取仓库详情 | 仓库链接 | topics 等详情 |
| 清洗 | `RegexCleaner` | 正则清洗和格式转换 | 网页文本 | 干净文本、star 数、版本号 |
| 清洗 | `SkillExtractor` | 提取技术关键词 | `RepoItem` | `SkillItem` 列表 |
| 并发 | `ConcurrentCrawler` | 单线程、线程池、进程池执行任务 | 任务列表 | 执行结果 |
| 并发 | `PerformanceTester` | 统计不同方式耗时 | 待测任务 | 性能对比结果 |
| 分析 | `Analyzer` | 排行、词频、趋势、技能差距 | 数据库查询结果 | 分析结论 |
| 可视化 | `Visualizer` | 生成柱状图、折线图、词云、雷达图 | 分析结论 | HTML 图表 |
| Web | `DashboardController` | 组织首页 dashboard | 数据库、分析器、可视化器 | 首页 HTML |
| Web | `SkillMatchController` | 组织技能对标页面 | 用户技能列表 | 雷达图和建议 |
| Web | `FlaskApp` | 绑定 Flask 路由 | Controller | Web 应用 |
| 集成 | `TrendPipeline` | 串联抓取、入库、分析和成果页生成 | 配置对象 | SQLite 数据库和成果页 |

## 3. 数据库表与类的对应关系

| 数据库表 | 对应类 | 用途 |
| --- | --- | --- |
| `repos` | `RepoItem` | 保存仓库基本信息 |
| `skills` | `SkillItem` | 保存技术关键词 |
| `trend_snapshot` | `TrendSnapshot` | 保存每天的趋势快照 |

## 4. 页面展示成果从哪里来

```text
真实 GitHub 仓库数据
        |
        v
repos / skills / trend_snapshot 三张表
        |
        v
Analyzer 统计
        |
        v
Visualizer 生成图表
        |
        v
DashboardController 和 SkillMatchController 组织页面
        |
        v
TrendPipeline 输出 outputs/dashboard.html
```

页面最终可以展示：热门仓库列表、编程语言排行、技能关键词词频、技术热度趋势、个人技能雷达图、建议学习方向。

交互页面还提供三个后端接口：

| 接口 | 作用 |
| --- | --- |
| `/api/summary` | 返回趋势概况 |
| `/api/skills` | 返回可勾选技术栈 |
| `/api/skill-match` | 根据用户勾选技能计算匹配度和学习建议 |

## 5. 真实抓取命令

```powershell
python run_pipeline.py --network --limit 15
```

严格验证真实抓取：

```powershell
python run_pipeline.py --network --strict-network --limit 15
```

## 6. 一分钟汇报稿

这个项目的类设计按数据流拆成六层：采集、清洗、存储、分析、可视化和 Web 展示。爬虫层的 `GithubTrendingSpider` 负责从 GitHub Trending 或 GitHub Search API 获取真实仓库数据，清洗层的 `RegexCleaner` 和 `SkillExtractor` 把文本变成结构化技能数据，存储层的 `DBManager` 统一写入 SQLite。后面 `Analyzer` 负责统计语言排行、关键词词频和技能差距，`Visualizer` 把结论变成图表，最后由 Controller 组织成页面。`TrendPipeline` 会把整条流程串起来并生成 `outputs/dashboard.html`，方便汇报展示。
