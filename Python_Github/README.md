# 开发者技术趋势画像与个人技能对标平台

这是一个用于课程 Stage2 类设计汇报的 Python 项目。它把 GitHub 数据抓取、正则清洗、SQLite 存储、数据分析、可视化和页面展示拆成多个职责清楚的类。

## 目录

- `tech_trend_platform/`：项目源码。
- `tests/`：每个模块的可演示测试。
- `Learning/`：面向汇报和自学的模块学习笔记，不参与项目运行。
- `docs/class_design.md`：纯 Markdown 版类设计说明，不依赖 Mermaid。
- `run_pipeline.py`：抓取数据、写入数据库、生成静态成果页。
- `app.py`：启动 Flask 后端，提供交互页面和 API。
- `outputs/dashboard.html`：最终可打开展示的成果页。
- `data/tech_trends.db`：SQLite 数据库。

## 快速运行

先跑测试：

```powershell
python -m unittest discover -s tests
```

使用示例数据生成成果页：

```powershell
python run_pipeline.py
```

抓取真实 GitHub 数据并生成成果页：

```powershell
python run_pipeline.py --network --limit 15
```

如果真实抓取失败时不想回退到示例数据，可以使用严格模式：

```powershell
python run_pipeline.py --network --strict-network --limit 15
```

设置自己的技能列表：

```powershell
python run_pipeline.py --network --skills Python,React,Docker
```

启动前后端交互页面：

```powershell
python app.py
```

启动后在浏览器打开：

```text
http://127.0.0.1:5000
```

页面会调用后端接口：

- `GET /api/summary`：趋势概况
- `GET /api/skills`：可勾选技术栈
- `POST /api/skill-match`：根据用户勾选技能计算匹配度和学习建议

生成后打开：

```text
outputs/dashboard.html
```

## 汇报时推荐展示

1. `docs/class_design.md`：讲清楚类设计和模块关系。
2. `Learning/`：展示每个模块对应的学习笔记。
3. `outputs/dashboard.html`：展示仓库表、语言排行、技能关键词、趋势图和个人技能对标结果。

## 数据来源说明

`run_pipeline.py --network` 会优先抓取 GitHub Trending 页面。如果 GitHub 页面结构变化导致解析失败，程序会使用 GitHub Search API 获取真实仓库数据作为兜底。
