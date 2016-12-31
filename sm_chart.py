#!/usr/bin/python

from small_multi import render_small_multiples, num_disp
from html import *
import sys
import argparse

# Capture tuples (subject, X, Y) from stdin, make charts and output
def main(argv):

    # Parse args
    ap = argparse.ArgumentParser(description='Render small-multiple charts from stdin data of form (subject, dimension, N).')
    ap.add_argument("-pbw", "--preferred-bar-width",
                    metavar="frac", type=float, help="use fraction of bar height as bar width")
    ap.add_argument("-ma", "--max-chart-aspect",
                    metavar="aspect", type=float, help="use aspect as max width as multiple height")
    ap.add_argument("-bs", "--bar-spacing",
                    metavar="frac", type=float, help="use fraction of bar width to space bars")
    ap.add_argument("-xt", "--x-axis-title",
                    metavar="text", help="title for X axis")
    ap.add_argument("-yt", "--y-axis-title",
                    metavar="text", help="title for Y axis")
    ap.add_argument("-t", "--totals", action="store_true",
                    help="show per-chart and grand totals")
    ap.add_argument("-s", "--sort", action="store_true",
                    help="sort charts by total")
    ap.add_argument("-n", "--top",
                    metavar="N", type=int, help="cut at top N, plus others")
    ap.add_argument("-xw", "--width",
                    metavar="W", type=float, help="use width W")
    ap.add_argument("-yh", "--height",
                    metavar="H", type=float, help="use height H")
    ap.add_argument("-sc", "--scale",
                    metavar="factor", type=float, help="scale charts by factor")
    ap.add_argument("-smt", "--sm-title",
                    metavar="text", help="title for chart collection")
    ap.add_argument("-sub", "--subject-file",
                    metavar="fn", help="file mapping subject to color [, title]")
    ap.add_argument("-lab", "--label-file",
                    metavar="fn", help="file mapping X value to color [, label]")
    ap.add_argument("-preserve", "--preserve-order", action="store_true",
                    help="try to preserve input order of X labels")
    ap.add_argument("-nl", "--newline",
                    metavar="str", help="use str as newline escape as well as \\n")
    args = ap.parse_args()

    # print str(args)

    # Load maps of subjects/labels to color and title
    subject_map = load_map_file(args.subject_file)
    label_map = load_map_file(args.label_file)

    # Read lines of standard in
    # Capture subjects in order of arrival
    subjects = []
    subj_data = {}
    lines = sys.stdin.readlines()
    grand_total = 0
    for line in lines:
        if not line or len(line) == 0:
            continue;
        line = line.strip()
        flds = line.split("\t")
        if len(flds) != 3:
            raise Exception("Line is not of form (subject, X, Y):\n" + line)
        (s, x, y) = flds
        if s not in subj_data:
            subjects.append(s)
            # Get chart color and title from subject map
            ctitle = s
            chart_opts = None
            if s in subject_map:
                if "label" in subject_map[s]:
                    ctitle = subject_map[s]["label"]
                if "color" in subject_map[s]:
                    chart_opts = {"data_color": subject_map[s]["color"]}
            # Init subject data
            subj_data[s] = {"title": ctitle, "data": []}
            # Get chart color from subject map
            if chart_opts:
                subj_data[s]["chart_opts"] = chart_opts

        # Get X info
        cinf = {"value": float(y)}
        # Use label map
        xlabel = x
        if x in label_map:
            if "label" in label_map[x]:
                xlabel = label_map[x]["label"]
            if "color" in label_map[x]:
                cinf["color"] = label_map[x]["color"]
        cinf["label"] = unescape_newlines(xlabel, args.newline)
        
        subj_data[s]["data"].append(cinf)
        grand_total += float(y)

    # Compile chart data in order
    data = []
    for s in subjects:
        data.append(subj_data[s])

    # Get chart options
    opts = {}
    adict = args.__dict__
    chart_opts = [
        "preferred_bar_width",
        "bar_spacing",
        "max_chart_aspect",
        "x_axis_title",
        "y_axis_title"
        ]
    for k, v in adict.iteritems():
        # Ignore non-chart options
        if k in chart_opts and v is not None:
            opts[k] = v

    # Render
    preserveAspectRatio = "xMinYMin"
    code = render_small_multiples(data, args.width, args.height, preserveAspectRatio,
                                  scale=args.scale, sort=args.sort, top=args.top, preserve_order=args.preserve_order,
                                  totals=args.totals, chart_opts=opts)

    # Exit status is 0 if data was printed, 1 otherwise
    if len(data) > 0:
        gt = ""
        if args.totals:
            gt = " (" + num_disp(grand_total) + ")"
        print h_h2(args.sm_title + gt, style="font-family: Arial")
        print code
        return 0
    return 1

# Un-escape newlines in titles
def unescape_newlines(s, repl):
    # First do the standard one
    s = s.replace("\\n", "\n")
    if repl is not None:
        s = s.replace(repl, "\n")
    return s

# Load map file
def load_map_file(fn):
    if not fn:
        return {}
    result = {}
    lines = ()
    with open(fn) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        flds = line.split("\t")
        if len(flds) >= 2:
            result[flds[0]] = {"color": flds[1]}
            if len(flds) >= 3:
                result[flds[0]]["label"] = flds[2]
    return result

# Do it
sys.exit(main(sys.argv))
sys.exit(2)
