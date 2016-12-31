#!/usr/bin/python
# Copyright 2014-2016 John K. Hinsdale

from svgtag import st_style, st_svg, st_text, st_rect, st_line, st_coords, pp
from chart import Chart
from random import uniform

def main():
    chart = Chart()
    chart.chart_title = "Sherry Halford"
    chart.y_axis_title = "Correct answers"
    chart.x_axis_title = "Assessment Period"
    chart.max_chart_aspect = 2

    n = int(uniform(0, 50.0))
    m = int(uniform(1, 1000000))
    n = 20
    chart.data = []
    for i in range(0,n):
        chart.data.append({"value": uniform(1,m), "label": "2011\nBOY\nP" + str(i)})

    print chart.render_style()
    for foo in range(0,3):
        print chart.render_svg(width=1000, height=800, preserveAspectRatio="xMinYMin")
    
main()

