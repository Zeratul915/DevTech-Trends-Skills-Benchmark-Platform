# 08 Web展示模块学习

## 对应类

- `DashboardController`
- `SkillMatchController`
- `FlaskApp`

## 类职责

`DashboardController` 负责首页 dashboard 内容。

`SkillMatchController` 负责个人技能对标页面。

`FlaskApp` 负责把控制器接到 Flask 路由上。

## 汇报重点

Web 层只负责请求和响应，不直接抓网页、不直接写 SQL、不直接做复杂分析。

## 路由设计

- `/`：首页 dashboard。
- `/skill-match`：个人技能对标页面。
- `/api/trend`：趋势数据接口。
