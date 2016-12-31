#!/usr/bin/python

from small_multi import render_small_multiples
from random import uniform
from html import *

# Capture data and render HTML page with small multiples charts
def main():
    
    nchart = 20
    nx = 3
    sm_title = "Comparison of student performance trends, 2010 - 2015"
    totals = True
    scale = None
    
    # Generate sequences of data
    time_chart = False
    mix_chart = True

    data = []
    opts = {}
    if time_chart:
        opts = {"x_axis_title": "Assessment period", "y_axis_title": "Correct answers"}
        for i in range(0, nchart):
            cdata = []
            # Max value for individual chart varies
            cmax = uniform(1, 5000)
            for x in range(0, nx):
                maybe = uniform(0, 1)
                if maybe >= 0.2:
                    cmaybe = uniform(0, 1)
                    if cmaybe <= 0.5:
                        color = "red"
                    else:
                        color = None
                    cdata.append({"value": int(uniform(0, cmax)), "label": "X" + str(x) + "\nFoo", "color": color})
            data.append({"title": "Chart #" + str(i), "data": cdata})
    elif mix_chart:
        sm_title = "Student Proficiency Composition by Class"
        totals = False
        opts = {"x_axis_title": "Assessment Outcome\nSource: foobar\nAnd toher", "y_axis_title": "% Students","preferred_bar_width": 30, "bar_spacing": .3}
        titles = ["Mrs.\nCooke", "Mr. Reynolds", "Ms. Chang", "Mrs. Russell", "Mr. Norman",
                  "Ms. Janet", "Mrs. Williams", "Ms. O'Donnell", "Mrs. Melnick", "Ms. Boren",
                  "Ms. Angela", "Mrs. Zeist", "Mr. Manning", "Ms. Ottavio", "Ms. Yu",
                  "Mrs. Somnowitcz", "Ms. Yurkisian", "Mr. Fischer", "Ms. Ramanathan", "Mrs. Pulian",
                  ]
                  
        for i in range(0, nchart):
            cdata = []
            pct_ok = uniform(30, 95)
            pct_border = uniform(20, 100 - pct_ok)
            pct_fail = 100 - pct_ok - pct_border
            mix = "e0"
            red = "#" + mix + "0000"
            yellow = "#" + mix + mix + "00"
            green = "#00" + mix + "00"
            cdata.append({"value": pct_fail, "label": "Not\nProficient", "color": red})
            cdata.append({"value": pct_border, "label": "Somewhat\nProficient", "color": yellow})
            cdata.append({"value": pct_ok, "label": "Proficient", "color": green})
            data.append({"title": titles[i], "data": cdata})
        def sortit(ainf, binf):
            a = [cinf["value"] for cinf in ainf["data"]]
            b = [cinf["value"] for cinf in binf["data"]]
            return cmp(b[2] * 1.5 + b[1], a[2] * 1.5 + a[1])
        data.sort(cmp=sortit)
        
    # Render
    preserveAspectRatio = "xMinYMin"
    code = render_small_multiples(data, None, None, preserveAspectRatio, preserve_order=True, scale=scale, sort=False, totals=totals, chart_opts=opts)
    print h_h2(sm_title, style="font-family: Arial")
    print code

# Do it
main()
