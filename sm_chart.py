#!/usr/bin/env python3

import argparse
import sys

from small_multi import render_small_multiples, num_disp, total_order
from htmltag import h_h2, h_p
from svgtag import _esc_text


DEFAULT_CHART_BLUE = "#0099ff"


def main(argv):
    ap = argparse.ArgumentParser(
        description='Render small-multiple charts from stdin data of form (subject, dimension, N).')
    input_opts = ap.add_argument_group("Input")
    output_opts = ap.add_argument_group("Output")
    format_opts = ap.add_argument_group("Format Options")

    format_opts.add_argument("-pbw", "--preferred-bar-width", metavar="frac", type=float,
                    help="Use fraction of bar height as bar width")
    format_opts.add_argument("-ma", "--max-chart-aspect", metavar="aspect", type=float,
                    help="Use aspect as max width as multiple height")
    format_opts.add_argument("-bs", "--bar-spacing", metavar="frac", type=float,
                    help="Use fraction of bar width to space bars")
    format_opts.add_argument("-xt", "--x-axis-title", metavar="text", help="Title for X axis")
    format_opts.add_argument("-yt", "--y-axis-title", metavar="text", help="Title for Y axis")
    format_opts.add_argument("-t", "--totals", action="store_true", help="Show per-chart and grand totals")
    format_opts.add_argument("-s", "--sort", action="store_true", help="Sort charts by total")
    format_opts.add_argument("-n", "--top", metavar="N", type=int, help="Cut at top N, plus others")
    output_opts.add_argument("-xw", "--width", metavar="W", type=float, help="Use width W")
    output_opts.add_argument("-yh", "--height", metavar="H", type=float, help="Use height H")
    output_opts.add_argument("-sc", "--scale", metavar="factor", type=float, help="Scale charts by factor")
    format_opts.add_argument("-smt", "--sm-title", metavar="text", help="Title for chart collection")
    format_opts.add_argument("-S", "--summary", action="store_true",
                    help="Show chart count plus X/Y ranges under the title")
    input_opts.add_argument("-sub", "--subject-file", metavar="fn", help="File mapping subject to color [, title]")
    input_opts.add_argument("-lab", "--label-file", metavar="fn", help="File mapping X value to color [, label]")
    input_opts.add_argument("-preserve", "--preserve-order", action="store_true",
                    help="Try to preserve input order of X labels")
    input_opts.add_argument("-nl", "--newline", metavar="str",
                    help="Use str as newline escape as well as \\n")
    format_opts.add_argument("-cbs", "--color-by-sign", action="store_true",
                    help="Color positive bars with --pos-color and negative bars with --neg-color "
                         "(label-file color still wins)")
    format_opts.add_argument("--pos-color", metavar="color", default="#3399cc",
                    help="Bar color for positive values when --color-by-sign is on (default %(default)s)")
    format_opts.add_argument("--neg-color", metavar="color", default="#cc3333",
                    help="Bar color for negative values when --color-by-sign is on (default %(default)s)")
    args = ap.parse_args(argv[1:])

    subject_map = load_map_file(args.subject_file)
    label_map = load_map_file(args.label_file)

    subjects = []
    subj_data = {}
    grand_total = 0.0
    y_min = None
    y_max = None
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        flds = line.split("\t")
        if len(flds) != 3:
            raise Exception("Line is not of form (subject, X, Y):\n" + line)
        s, x, y = flds
        if s not in subj_data:
            subjects.append(s)
            ctitle = s
            chart_opts = None
            if s in subject_map:
                if "label" in subject_map[s]:
                    ctitle = subject_map[s]["label"]
                if "color" in subject_map[s]:
                    chart_opts = {"data_color": subject_map[s]["color"]}
            subj_data[s] = {"title": ctitle, "data": []}
            if chart_opts:
                subj_data[s]["chart_opts"] = chart_opts

        yval = float(y)
        if y_min is None or yval < y_min:
            y_min = yval
        if y_max is None or yval > y_max:
            y_max = yval
        cinf = {"value": yval}
        xlabel = x
        if x in label_map:
            if "label" in label_map[x]:
                xlabel = label_map[x]["label"]
            if "color" in label_map[x]:
                cinf["color"] = label_map[x]["color"]
        # Sign-based coloring fills in where label_map did not set an explicit color
        if args.color_by_sign and "color" not in cinf:
            cinf["color"] = args.neg_color if yval < 0 else args.pos_color
        cinf["label"] = unescape_newlines(xlabel, args.newline)
        subj_data[s]["data"].append(cinf)
        grand_total += yval

    data = [subj_data[s] for s in subjects]
    label_seqs = [[item["label"] for item in subj_data[s]["data"]] for s in subjects]

    # Forward only the named chart options to the chart layer
    chart_opt_names = ("preferred_bar_width", "bar_spacing", "max_chart_aspect",
                       "x_axis_title", "y_axis_title")
    adict = vars(args)
    opts = {k: adict[k] for k in chart_opt_names if adict.get(k) is not None}

    preserveAspectRatio = "xMinYMin"
    code = render_small_multiples(data, args.width, args.height, preserveAspectRatio,
                                  scale=args.scale, sort=args.sort, top=args.top,
                                  preserve_order=args.preserve_order,
                                  totals=args.totals, chart_opts=opts)

    if data:
        print(h_h2(build_title(args.sm_title or "", grand_total, args.totals),
                   style="font-family: Arial"))
        if args.summary:
            print(h_p(build_summary(args, data, label_seqs, y_min, y_max),
                      style="font-family: Arial"))
        print(code)
        return 0
    return 1


def unescape_newlines(s, repl):
    s = s.replace("\\n", "\n")
    if repl is not None:
        s = s.replace(repl, "\n")
    return s


def load_map_file(fn):
    if not fn:
        return {}
    result = {}
    with open(fn) as f:
        for line in f:
            line = line.strip()
            flds = line.split("\t")
            if len(flds) >= 2:
                result[flds[0]] = {"color": flds[1]}
                if len(flds) >= 3:
                    result[flds[0]]["label"] = flds[2]
    return result


def build_title(title, grand_total, totals):
    result = _esc_text(title)
    if totals:
        result += " " + blue("(" + num_disp(grand_total) + ")")
    return result


def build_summary(args, data, label_seqs, y_min, y_max):
    labels = total_order(label_seqs, preserve_order=args.preserve_order)
    x_from = labels[0] if labels else ""
    x_to = labels[-1] if labels else ""
    x_title = args.x_axis_title or "X"
    y_title = args.y_axis_title or "Y"
    y_min_label = value_with_unique_subject(y_min or 0, data)
    y_max_label = value_with_unique_subject(y_max or 0, data)
    sep = " &bull; "
    return sep.join((
        "%s charts" % blue(rendered_chart_count(len(data), args.top)),
        "%s: %s - %s" % (_esc_text(x_title), blue(x_from), blue(x_to)),
        "%s: %s - %s" % (_esc_text(y_title), blue(y_min_label), blue(y_max_label)),
    ))


def value_with_unique_subject(value, data):
    matches = []
    for chart in data:
        for item in chart["data"]:
            v = item.get("value")
            if v is None:
                continue
            if float(v) == float(value):
                matches.append((chart.get("title") or "", item.get("label")))
                if len({subject for subject, label in matches}) > 1:
                    return num_disp(value)
    if matches:
        subject = matches[0][0]
        if subject:
            labels = [label for match_subject, label in matches
                      if match_subject == subject and label is not None]
            if labels:
                return "%s (%s, %s)" % (num_disp(value), subject, min(labels))
            return "%s (%s)" % (num_disp(value), subject)
    return num_disp(value)


def blue(value):
    return '<span style="color: %s">%s</span>' % (DEFAULT_CHART_BLUE, _esc_text(value))


def rendered_chart_count(data_count, top):
    if top is not None and 0 < top < data_count:
        return top + 1
    return data_count


if __name__ == "__main__":
    sys.exit(main(sys.argv))
