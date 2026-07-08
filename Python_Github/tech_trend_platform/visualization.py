from __future__ import annotations

from html import escape


class Visualizer:
    """Builds chart HTML snippets; uses pyecharts when available."""

    def bar_chart(self, title: str, data: list[tuple[str, int]]) -> str:
        try:
            from pyecharts import options as opts
            from pyecharts.charts import Bar

            chart = Bar().add_xaxis([x for x, _ in data]).add_yaxis("数量", [y for _, y in data])
            chart.set_global_opts(title_opts=opts.TitleOpts(title=title))
            return chart.render_embed()
        except Exception:
            return self._simple_list(title, data)

    def line_chart(self, title: str, series: dict[str, list[tuple[str, int]]]) -> str:
        try:
            from pyecharts import options as opts
            from pyecharts.charts import Line

            x_axis = sorted({date for values in series.values() for date, _ in values})
            chart = Line().add_xaxis(x_axis)
            for name, values in series.items():
                point_map = dict(values)
                chart.add_yaxis(name, [point_map.get(date, 0) for date in x_axis])
            chart.set_global_opts(title_opts=opts.TitleOpts(title=title))
            return chart.render_embed()
        except Exception:
            rows = [(name, len(values)) for name, values in series.items()]
            return self._simple_list(title, rows)

    def radar_chart(self, title: str, industry_scores: dict[str, int], user_skills: list[str]) -> str:
        user_set = {skill.lower() for skill in user_skills}
        data = [
            (skill, 100 if skill.lower() in user_set else 20)
            for skill in industry_scores.keys()
        ]
        return self._simple_list(title, data)

    def word_cloud(self, title: str, data: list[tuple[str, int]]) -> str:
        try:
            from pyecharts import options as opts
            from pyecharts.charts import WordCloud

            chart = WordCloud().add("", data)
            chart.set_global_opts(title_opts=opts.TitleOpts(title=title))
            return chart.render_embed()
        except Exception:
            return self._simple_list(title, data)

    @staticmethod
    def _simple_list(title: str, data: list[tuple[str, int]]) -> str:
        items = "".join(f"<li>{escape(str(name))}: {value}</li>" for name, value in data)
        return f"<div class=\"chart-card\"><h3>{escape(title)}</h3><ul>{items}</ul></div>"
