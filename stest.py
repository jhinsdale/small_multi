#!/usr/bin/env python3

from random import uniform

from chart import Chart


def main():
    chart = Chart()
    chart.chart_title = "Sherry Halford"
    chart.subject = "Sherry Halford"
    chart.y_axis_title = "Correct answers"
    chart.x_axis_title = "Assessment Period"
    chart.max_chart_aspect = 2

    n = 20
    m = int(uniform(1, 1_000_000))
    chart.data = []
    for i in range(n):
        # Mix in some negative values to exercise the new feature
        v = uniform(1, m) if uniform(0, 1) > 0.3 else -uniform(1, m / 2)
        chart.data.append({"value": v, "label": "2011\nBOY\nP" + str(i)})

    print(chart.render_style())
    for _ in range(3):
        print(chart.render_svg(width=1000, height=800, preserveAspectRatio="xMinYMin"))


if __name__ == "__main__":
    main()
